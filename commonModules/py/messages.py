from boto3.session import Session
from flask import request, render_template,jsonify,json
import os

class Msg():


  def __init__(self):
    """ Usage Message """

    with open('../config/help.json') as json_data:
     self.api = json.load(json_data)
    self.agent = None
    if 'Mozilla' in request.headers.get('User-Agent'): self.agent = 'html'
    self.help = render_template('help.html', html = self.agent, api = self.api)    


  def message(self, msg, code):
    """ Return Status Message """

    resp_json = { 'Status': code, 'Message': msg, }
    if self.agent == None:
      resp = jsonify(resp_json)
      resp.status_code = code
    else:
      resp_format = json.dumps(resp_json ,sort_keys = True, indent = 4)
      resp = render_template('messages.html', code = code, msg = resp_format), code

    return resp
