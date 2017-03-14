"""
  API to create a VPC required for ETHOS Single Tenant Onboarding
  Automation Squad Id:
 
  Reference:
    https://wiki.corp.adobe.com/display/cloudops/ETHOS+Single+Tenant+Onboarding+Steps
"""

from flask import Flask, jsonify, request
from commonModules.py.credentials import Auth
from commonModules.py.messages import Msg
from aws import Aws
import jinja2


app = Flask(__name__)

my_loader = jinja2.ChoiceLoader([
  app.jinja_loader,
  jinja2.FileSystemLoader('commonModules/py/templates'),
])
app.jinja_loader = my_loader


# API Parameters
#
def region():
  region = request.args.get('region')
  if (region == None) or (region == ''):
    region = 'help'
  return region

def vpc_id():
  vpc_id = request.args.get('vpc-id')
  if (vpc_id == None) or (vpc_id == ''):
    vpc_id = 'help'
  return vpc_id

def cidr():
  cidr = request.args.get('cidr')
  if (cidr == None) or (cidr == ''):
    cidr = 'help'
  return cidr

def azs():
  azs = request.args.get('azs')
  if (azs == None) or (azs == ''):
    azs = 'help'
  return azs

def name():
  name = request.args.get('name')
  if (name == None) or (name == ''):
    name = 'help'
  return name

def env():
  env = request.args.get('env')
  if (env == None) or (env == ''):
    env = 'help'
  return env

def creds(region):
  creds = Auth().check_creds(Aws(region).session)
  return creds

askfor = { 'region':region,
           'vpc_id':vpc_id,
           'cidr'  :cidr,
           'azs'   :azs,
           'name'  :name,
           'env'   :env,
           'creds' :creds
         }


@app.route('/vpc/check', methods = ['GET'])
def check():

  region = askfor['region']()
  cidr   = askfor['cidr']()

  usr = Msg()
  for arg in [region, cidr]:
    if arg == 'help': return usr.help

  creds  = askfor['creds'](region)
  if creds != 'Pass': return usr.message(creds, 401)

  aws = Aws(region)
  vpc_id = None
  vpc = aws.get_vpc(cidr, vpc_id)
  if vpc:
    return usr.message(vpc, 200)

  return usr.message('VPC assigned ' + str(cidr) + ' does not exist.', 200)

@app.route('/vpc/create', methods = ['GET'])
def create():

  region = askfor['region']()
  cidr   = askfor['cidr']()
  azs    = askfor['azs']()
  name   = askfor['name']()
  env    = askfor['env']()

  usr = Msg()
  for arg in [region, cidr, azs, name, env]:
    if arg == 'help': return usr.help

  creds  = askfor['creds'](region)
  if creds != 'Pass': return usr.message(creds, 401)

  aws = Aws(region)
  subnets = aws.subnet_sizes(azs, cidr)
  if 'error' in subnets:
    return usr.message(subnets, 404)

  vpc, vpc_id = aws.create_vpc(cidr, region, name, env)
  if 'error' in vpc:
    return usr.message(vpc, 400)

  igw, igw_id = aws.create_igw(vpc_id, region, name, env)
  if 'error' in igw:
    if vpc_id != 'None': aws.delete_vpc(vpc_id)
    return usr.message(igw, 400)

  sub_ids = aws.create_subnet(vpc_id, azs, subnets, region, name, env)
  rtb_ids = aws.create_rtb(vpc_id, azs, sub_ids, igw_id, region, name, env)
  acl_ids = aws.create_acl(vpc_id, azs, sub_ids, cidr, region, name, env)

  return usr.message(vpc, 200)

@app.route('/vpc/delete', methods = ['GET'])
def delete():

  region = askfor['region']()
  vpc_id = askfor['vpc_id']()

  usr = Msg()
  for arg in [region, vpc_id]:
    if arg == 'help': return usr.help

  creds  = askfor['creds'](region)
  if creds != 'Pass': return usr.message(creds, 401)

  aws = Aws(region)
  cidr = None
  vpc = aws.get_vpc(cidr, vpc_id)
  if vpc:
    aws.delete_igw(vpc_id)
    aws.delete_subnet(vpc_id)
    aws.delete_rtb(vpc_id)
    aws.delete_acl(vpc_id)
    aws.delete_vpc(vpc_id)
  else:
    return usr.message(vpc_id + ' does not exist.', 200)

  return usr.message(vpc_id + ' removed.', 200)


@app.errorhandler(404)
def not_found(error=None):

  usr = Msg()
  resp = usr.message('Not Found: ' + request.url, 404)

  return resp


@app.route('/')
def root():
  return Msg().help

@app.route('/vpc/', strict_slashes=False)
def index():
  return Msg().help

@app.route('/vpc/help/', strict_slashes=False)
def help():
  return Msg().help

@app.route('/vpc/ping/', strict_slashes=False)
def ping():
  aws = Aws('us-east-1'); usr = Msg()
  return usr.message(aws.msg, 200)


if __name__ == "__main__":
    app.run(debug = False, host = '0.0.0.0')
