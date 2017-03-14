from aws import Aws
import boto3
from moto import mock_ec2

region = 'us-east-1'
cidr = '10.10.10.0/23'
sub = '10.10.10.0/25'
name = 'testing'
env = 'dev'
azs = '2'

@mock_ec2
def test_create_vpc():

  session = boto3.Session(region_name = region)
  ec2 = session.client('ec2')
  
  # Test...
  aws = Aws(region)
  aws.create_vpc(cidr, region, name, env)

  assert ec2.describe_vpcs(Filters=[{ 'Name': 'cidr', 'Values': [ cidr ] }])['Vpcs'][0]['CidrBlock'] == cidr


@mock_ec2
def test_delete_vpc():

  session = boto3.Session(region_name = region)
  ec2 = session.client('ec2')

  vpc_id = ec2.create_vpc(CidrBlock=cidr)['Vpc']['VpcId']

  # Test...
  aws = Aws(region)
  aws.delete_vpc(vpc_id)

  assert ec2.describe_vpcs(Filters=[{ 'Name': 'vpc-id', 'Values': [ vpc_id ] }])['Vpcs'] == []


@mock_ec2
def test_create_igw():

  session = boto3.Session(region_name = region)
  ec2 = session.client('ec2')

  vpc_id = ec2.create_vpc(CidrBlock=cidr)['Vpc']['VpcId']

  # Test...
  aws = Aws(region)
  aws.create_igw(vpc_id, region, name, env)

  assert ec2.describe_internet_gateways(Filters=[{ 'Name': 'attachment.vpc-id', 'Values': [ vpc_id ] }])['InternetGateways'][0]['Attachments'][0]['VpcId'] == vpc_id


@mock_ec2
def test_delete_igw():

  session = boto3.Session(region_name = region)
  ec2 = session.client('ec2')

  vpc_id = ec2.create_vpc(CidrBlock=cidr)['Vpc']['VpcId']
  igw_id = ec2.create_internet_gateway()['InternetGateway']['InternetGatewayId']

  ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)

  # Test...
  aws = Aws(region)
  aws.delete_igw(vpc_id)

  assert ec2.describe_internet_gateways(Filters=[{ 'Name': 'attachment.vpc-id', 'Values': [ vpc_id ] }])['InternetGateways'] == []


@mock_ec2
def test_create_subnet():

  session = boto3.Session(region_name = region)
  ec2 = session.client('ec2')

  vpc_id = ec2.create_vpc(CidrBlock=cidr)['Vpc']['VpcId']

  # Test...
  aws = Aws(region)
  subnets = aws.subnet_sizes(azs, cidr)
  aws.create_subnet(vpc_id, azs, subnets, region, name, env) 

  assert ec2.describe_subnets(Filters=[{ 'Name': 'cidrBlock', 'Values': [ sub ] } ])['Subnets'][0]['CidrBlock'] == sub


@mock_ec2
def test_delete_subnet():

  session = boto3.Session(region_name = region)
  ec2 = session.client('ec2')

  vpc_id = ec2.create_vpc(CidrBlock=cidr)['Vpc']['VpcId']
  sub_id = ec2.create_subnet(VpcId=vpc_id, CidrBlock=sub)['Subnet']['SubnetId']

  # Test...
  aws = Aws(region)
  aws.delete_subnet(vpc_id)

  assert ec2.describe_subnets(SubnetIds=[ sub_id ])['Subnets'] == []

