# Makefile
#
PROJECT=hamapi
SERVICE=flask-vpc

# During the process of building an image Docker will step through the instructions
# in your Dockerfile executing each in the order specified. As each instruction is
# examined Docker will look for an existing image in its cache that it can reuse,
# rather than creating a new (duplicate) image. If you do not want to use the cache
# at all you can use the --no-cache=true option on the docker build command.

help:
	@echo ""
	@echo "Use \`make <target>\` where <target> is one of:"
	@echo "  build                  builds the docker image"
	@echo "  build-no-cache         builds the docker image with the '--no-cache=true option'"
	@echo "  run                    creates and starts the docker container in the background (note: build the image prior to run)"
	@echo "  test                   runs the application test suite"
	@echo "  clean                  stops and removes the docker container"
	@echo ""

clean:
	docker-compose -p $(PROJECT) stop $(SERVICE) && docker-compose -p $(PROJECT) rm -f $(SERVICE)

build:
	docker-compose -p $(PROJECT) build $(SERVICE)

build-no-cache:
	docker-compose -p $(PROJECT) build --no-cache $(SERVICE)

run:
	docker-compose -p $(PROJECT) up -d $(SERVICE)

ci:	test

test:
	cd ./app && python3 -m pytest ./test_vpc.py
