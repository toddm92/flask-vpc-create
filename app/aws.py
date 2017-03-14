from configparser import SafeConfigParser
from commonModules.py.credentials import Auth
from netaddr import *
import time


# Load default config
#
parser = SafeConfigParser()
parser.read('../config/vpc.ini')


class Aws():

  def __init__(self, region):
    """ Setup Environment Variables """

    self.msg = parser.get('vpc_config', 'PING_MSG')
    self.region = parser.get('vpc_config', 'REGION')

    auth = Auth()
    self.session = auth.get_creds(region)
    self.ec2 = self.session.client('ec2')

  def create_vpc(self, cidr, region, name, env):
    """ Create a VPC """

    vpc_id = 'None'

    try:
      vpc = self.ec2.create_vpc(CidrBlock=cidr, InstanceTenancy='default')['Vpc']
    except Exception as e:
      vpc = str(e)
    else:
      vpc_id = vpc.get('VpcId')

      self.ec2.modify_vpc_attribute(
        VpcId=vpc_id,
        EnableDnsSupport={ 'Value': True })
      self.ec2.modify_vpc_attribute(
        VpcId=vpc_id,
        EnableDnsHostnames={ 'Value': True })

      tag = self.short_region(name, env, 'vpc', region); self.tag_resource(vpc_id)

    return vpc, vpc_id

  def create_igw(self, vpc_id, region, name, env):
    """ Create an Internet gateway """

    igw_id = 'None'

    try:
      igw = self.ec2.create_internet_gateway()['InternetGateway']
    except Exception as e:
      igw = str(e)
    else:
      igw_id = igw.get('InternetGatewayId')

      self.ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
      tag = self.short_region(name, env, 'igw', region); self.tag_resource(igw_id)

    return igw, igw_id

  def subnet_sizes(self, azs, cidr):
    """
    Calculate Subnets Sizes

    Possible scenarios:
      a) /25 2AZ  (4 Subnets = /27)
      b) /24 2AZ  (4 Subnets = /26)
      c) /23 2AZ  (4 Subnets = /25)
      d) /22 2AZ  (4 Subnets = /24)
      e) /23 3AZ  (3 Subnets = /27, 3 Subnets = /25)
      f) /22 3AZ  (3 Subnets = /26, 3 Subnets = /24)
    """

    netmasks = ('255.255.252.0', '255.255.254.0', '255.255.255.0', '255.255.255.128')

    ip = IPNetwork(cidr)
    mask = ip.netmask

    if int(azs) == 3:
      if str(mask) not in netmasks[0:2]:
        return 'An error occurred: netmask ' + str(mask) + ' not allowed.'
    
      for n, netmask in enumerate(netmasks):
        if str(mask) == netmask:
          pub_net = list(ip.subnet(n + 24))
          pri_subs = pub_net[1:]
          pub_mask = pub_net[0].netmask
      
      pub_split = list(ip.subnet(26)) if (str(pub_mask) == '255.255.255.0') else list(ip.subnet(27))
      pub_subs = pub_split[:3]
  
      subnets = pub_subs + pri_subs

    elif int(azs) == 2:
      if str(mask) not in netmasks:
        return 'An error occurred: netmask ' + str(mask) + ' not allowed.'

      for n, netmask in enumerate(netmasks):
        if str(mask) == netmask:
          subnets = list(ip.subnet(n + 24))

    else:
      return 'An error occurred: ' + str(azs) + ' availability-zone(s) not allowed.'

    return subnets

  def create_subnet(self, vpc_id, azs, subnets, region, name, env):
    """ Create Subnets """

    zones = []
    all_zones = self.ec2.describe_availability_zones()['AvailabilityZones']

    for zone in all_zones:
      if zone.get('State') != 'available':
        continue
      zones.append(zone.get('ZoneName'))

    i = 0; tier = 'public'
    sub_ids = []
    for sub in subnets:
      subnet = self.ec2.create_subnet(VpcId=vpc_id, CidrBlock=str(sub), AvailabilityZone=zones[i])['Subnet']
      sub_id = subnet.get('SubnetId')
      i += 1; tag = self.short_region(name, env, tier + '-sub' + str(i), region); self.tag_resource(sub_id)

      sub_ids.append(sub_id)
      if i == int(azs): i = 0; tier = 'private'

    return sub_ids

  def create_rtb(self, vpc_id, azs, sub_ids, igw_id, region, name, env):
    """ Create Route Tables """

    i = 0; tier = 'public'
    rtb_ids = []
    for sub in sub_ids:
      if i == 0:
        rtb = self.ec2.create_route_table(VpcId=vpc_id)['RouteTable']
        rtb_id = rtb.get('RouteTableId')
        tag = self.short_region(name, env, tier + '-rtb', region); self.tag_resource(rtb_id)

        self.ec2.create_route(
          RouteTableId=rtb_id,
          DestinationCidrBlock='0.0.0.0/0',
          GatewayId=igw_id)

        rtb_ids.append(rtb_id)
      self.ec2.associate_route_table(RouteTableId=rtb_id, SubnetId=sub)
      i += 1
      if i == int(azs): i = 0; tier = 'private'

    return rtb_ids

  def create_acl(self, vpc_id, azs, sub_ids, cidr, region, name, env):
    """ Create Network Access Lists """

    i = 0; tier = 'public'
    acl_ids = []
    for sub in sub_ids:
      if i == 0:
        acl = self.ec2.create_network_acl(VpcId=vpc_id)['NetworkAcl']
        acl_id = acl.get('NetworkAclId')
        tag = self.short_region(name, env, tier + '-acl', region); self.tag_resource(acl_id)

        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=100,
          Protocol='-1',
          RuleAction='allow',
          CidrBlock=cidr,
          Egress=False
        )
        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=200,
          Protocol='6',
          RuleAction='allow',
          CidrBlock='0.0.0.0/0',
          Egress=False,
          PortRange={'From': 443, 'To': 443 }
        ) 
        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=300,
          Protocol='6',
          RuleAction='allow',
          CidrBlock='0.0.0.0/0',
          Egress=False,
          PortRange={'From': 80, 'To': 80 }
        )
        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=400,
          Protocol='6',
          RuleAction='allow',
          CidrBlock='0.0.0.0/0',
          Egress=False,
          PortRange={'From': 1024, 'To': 65535 }
        )
        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=500,
          Protocol='6',
          RuleAction='allow',
          CidrBlock='0.0.0.0/0',
          Egress=False,
          PortRange={'From': 22, 'To': 22 }
        )
        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=600,
          Protocol='17',
          RuleAction='allow',
          CidrBlock='0.0.0.0/0',
          Egress=False,
          PortRange={'From': 123, 'To': 123 }
        )

        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=100,
          Protocol='-1',
          RuleAction='allow',
          CidrBlock=cidr,
          Egress=True
        )
        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=200,
          Protocol='6',
          RuleAction='allow',
          CidrBlock='0.0.0.0/0',
          Egress=True,
          PortRange={'From': 443, 'To': 443 }
        ) 
        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=300,
          Protocol='6',
          RuleAction='allow',
          CidrBlock='0.0.0.0/0',
          Egress=True,
          PortRange={'From': 80, 'To': 80 }
        )
        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=400,
          Protocol='6',
          RuleAction='allow',
          CidrBlock='0.0.0.0/0',
          Egress=True,
          PortRange={'From': 1024, 'To': 65535 }
        )
        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=500,
          Protocol='6',
          RuleAction='allow',
          CidrBlock='0.0.0.0/0',
          Egress=True,
          PortRange={'From': 22, 'To': 22 }
        )
        self.ec2.create_network_acl_entry(
          NetworkAclId=acl_id,
          RuleNumber=600,
          Protocol='17',
          RuleAction='allow',
          CidrBlock='0.0.0.0/0',
          Egress=True,
          PortRange={'From': 123, 'To': 123 }
        )

        acl_ids.append(acl_id) 

      acl_filter = self.ec2.describe_network_acls(Filters=[{ 'Name': 'association.subnet-id', 'Values': [ sub ] }])
      acl_assocs = acl_filter['NetworkAcls'][0]['Associations']
      for assoc in acl_assocs:
        if sub == assoc.get('SubnetId'): assoc_id = assoc.get('NetworkAclAssociationId')
      self.ec2.replace_network_acl_association(NetworkAclId=acl_id, AssociationId=assoc_id)
      i += 1
      if i == int(azs): i = 0; tier = 'private'

    return acl_ids

  def delete_igw(self, vpc_id):
    """ Remove Internet gateway """

    igw = self.ec2.describe_internet_gateways(Filters=[{ 'Name': 'attachment.vpc-id', 'Values': [ vpc_id ] }])

    try:
      igw_id = igw['InternetGateways'][0]['InternetGatewayId']
    except KeyError as e:
      print(str(e))
    else:
      self.ec2.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
      self.ec2.delete_internet_gateway(InternetGatewayId=igw_id)

  def delete_subnet(self, vpc_id):
    """ Remove Subnets  """

    subnets = self.ec2.describe_subnets(Filters=[{ 'Name': 'vpc-id', 'Values': [ vpc_id ] } ])

    for sub in subnets['Subnets']:
      sub_id = sub.get('SubnetId', None)
      if sub_id != None:
        try:
          self.ec2.delete_subnet(SubnetId=sub_id)
        except Exception as e:
          print(str(e))

  def delete_rtb(self, vpc_id):
    """ Remove Route Tables  """

    rtbs = self.ec2.describe_route_tables(Filters=[{ 'Name': 'vpc-id', 'Values': [ vpc_id ] }])

    for rtb in rtbs['RouteTables']:
      if rtb['Associations']:
        continue
      rtb_id = rtb.get('RouteTableId', None)
      if rtb_id != None:
        self.ec2.delete_route_table(RouteTableId=rtb_id)

  def delete_acl(self, vpc_id):
    """ Delete Network Access Lists """

    acls = self.ec2.describe_network_acls(Filters=[{ 'Name': 'vpc-id', 'Values': [ vpc_id ] }])

    for acl in acls['NetworkAcls']:
      if acl.get('IsDefault') == True:
        continue
      acl_id = acl.get('NetworkAclId', None)
      if acl_id != None:
        try:
          self.ec2.delete_network_acl(NetworkAclId=acl_id)
        except Exception as e:
          print(str(e))

  def delete_vpc(self, vpc_id):
    """ Delete a VPC """

    try:
      self.ec2.delete_vpc(VpcId=vpc_id)
    except Exception as e:
      print(str(e))

  def get_vpc(self, cidr=None, vpc_id=None):
    """ Find a VPC """

    if cidr != None:
      vpc = self.ec2.describe_vpcs(Filters=[{ 'Name': 'cidr', 'Values': [ cidr ] }])['Vpcs']
    elif vpc_id != None:
      vpc = self.ec2.describe_vpcs(Filters=[{ 'Name': 'vpc-id', 'Values': [ vpc_id ] }])['Vpcs']
    else:
      vpc = None

    return vpc

  def short_region(self, name, env, resource, region):
    abbr = 'nul'
    if region == 'us-east-1':      abbr = 'ue1'
    if region == 'us-east-2':      abbr = 'ue2'
    if region == 'us-west-1':      abbr = 'uw1'
    if region == 'us-west-2':      abbr = 'uw2'
    if region == 'eu-west-1':      abbr = 'ew1'
    if region == 'eu-central-1':   abbr = 'ec1'
    if region == 'ap-northeast-1': abbr = 'an1'
    if region == 'ap-northeast-2': abbr = 'an2'
    if region == 'ap-southeast-1': abbr = 'as1'
    if region == 'ap-southeast-2': abbr = 'as2'
    if region == 'ap-south-1':     abbr = 'as1'
    if region == 'sa-east-1':      abbr = 'se1'

    self.name = name + '-' + env + '-' + resource + '-' + abbr

  def tag_resource(self, resource_id):
    time.sleep(.500)
    try:
      self.ec2.create_tags(Resources=[ resource_id ], Tags=[ { 'Key':'Name', 'Value':self.name } ])
    except Exception as e:
      print(str(e))

