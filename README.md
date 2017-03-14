# deploymentVPC

**API to create a VPC required for ETHOS Single Tenant Onboarding**

:dart: To clone this repo and submodules use:

`git clone --recursive git@git.corp.adobe.com:hamapi/deploymentVPC-API.git`

### Requirements
* boto3 v1.4.0
* flask v0.11.1
* netaddr v0.7.18

:notebook: refer to `app/requirements.txt` for the full list of requirements

For testing:
* pytest
* moto

### Prerequisites

AWS temporary KLAM Credentials. 

1. Use your **admin_and_support** policy and **default (1 hour)** duration access
2. Select "GET CLI"
3. From the "in BASH" section; Copy to clipboard
4. Copy from the clipboard to your Shell  (Cmd-V MacOS)

### Docker Setup
```
Use `make <target>` where <target> is one of:
  build                  builds the docker image
  build-no-cache         builds the docker image with the '--no-cache=true option'
  run                    creates and starts the docker container in the background
  clean                  stops and removes the docker container
```
### API Usage
```
DESCRIPTION: Create a VPC required for ETHOS Single Tenant Onboarding

FORMAT: curl http://127.0.0.1:<port>/vpc/<action>

DETAILS:

  Action: /check
     Description: checks for the existence of a VPC
     Parameters: [ region=<region_name>, cidr=<cidr_block> ]
     Optional Parameters: none

  Action: /create
     Description: creates a VPC
     Parameters: [ region=<region_name>, cidr=<cidr_block>, azs=<no_of_azs>, name=<project/api_name>, env=<env> ]
     Optional Parameters: none

  Action: /delete
     Description: removes a VPC
     Parameters: [ region=<region_name>, vpc-id=<vpc_id> ]
     Optional Parameters: none

  Action: /ping
     Description: ping the API
     Parameters: none
     Optional Parameters: none

  Action: /help
     Description: prints this message
     Parameters: none
     Optional Parameters: none
```

Example:

```
curl http://127.0.0.1:5000/vpc/create?region=us-west-2\&cidr=10.10.10.0/23\&azs=3\&name=cloudops\&env=dev
```

### Testing
```
make test
```

### References

Squad:
* https://wiki.corp.adobe.com/display/cloudops/ETHOS+Single+Tenant+Onboarding+Steps

Python:
* http://pytest.org/latest/
* https://github.com/spulec/moto
* http://flask.pocoo.org/

Docker:
* https://docs.docker.com/docker-for-mac/
* https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/
* http://containertutorials.com/docker-compose/flask-simple-app.html
