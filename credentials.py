from boto3.session import Session
import os

class Auth():

  def get_creds(self, region):

    keyid = os.environ.get('AWS_ACCESS_KEY_ID')
    secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
    token = os.environ.get('AWS_SESSION_TOKEN')

    session = Session(aws_access_key_id = keyid, aws_secret_access_key = secret, aws_session_token = token, region_name = region)
 
    return session

  def check_creds(self, session):
    """ Check AWS Credentials """

    iam = session.client('iam')

    try:
      creds = iam.get_account_summary()
    except Exception as e:
      creds = str(e)
    else:
      creds = 'Pass'

    if creds != 'Pass':
      errors = { 'InvalidClientTokenId'  : 'An error occurred (InvalidClientTokenId): Please choose the one-hour credentials',
                 'AuthFailure'           : 'An error occurred (AuthFailure): AWS was not able to validate the provided access credentials',
                 'ExpiredToken'          : 'An error occurred (ExpiredToken): The security token included in the request is expired',
                 'SignatureDoesNotMatch' : 'An error occurred (SignatureDoesNotMatch): The request signature does not match the one provided',
                 'Could not connect to the endpoint URL' : creds
               }

      for key, value in errors.items():
        if key in creds: creds = value

    return creds
