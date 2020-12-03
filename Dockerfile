FROM python:3.8-slim as base
MAINTAINER Flywheel <support@flywheel.io>

ENV FLYWHEEL="/flywheel/v0"

COPY ["requirements.txt", "/opt/requirements.txt"]
#DEV install git
RUN apt-get update && apt-get install -y git && \ 
    pip install -r /opt/requirements.txt && \
    mkdir -p $FLYWHEEL

COPY run.py manifest.json $FLYWHEEL/
COPY flywheel_hierarchy_curator $FLYWHEEL/flywheel_hierarchy_curator

WORKDIR $FLYWHEEL
