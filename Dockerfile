# Dockerfile best practices
# https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/

# Set the base image
FROM python:3.5.1

# Author
MAINTAINER Todd "toddm92@gmail.com"

# Set environment variables for “descendant” Dockerfile commands
ENV root /vpc
ENV api ${root}/app

# Copy new files or directories from <src> and add them to the filesystem of the container
COPY . ${root}

# Sets the working directory for any RUN, CMD, ENTRYPOINT, COPY and ADD instructions that follow it in the Dockerfile
WORKDIR ${api}

# Execute commands in a new layer on top of the current image and commit the results
RUN pip install -r requirements.txt

# API Health
HEALTHCHECK --interval=5s --timeout=3s CMD curl --fail http://127.0.0.1:5000/vpc/ping || exit 1

# The executable
ENTRYPOINT ["python"]

# Specify the intended command for the image ("Defaults" for an executing container)
#   Note: `docker run` arguments will override the defaults
CMD ["vpc.py"]
