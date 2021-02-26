FROM python:3.8-slim as base

ENV FLYWHEEL="/flywheel/v0"
WORKDIR ${FLYWHEEL}

#DEV install git
RUN apt-get update && apt-get install -y git && \ 
    pip install "poetry==1.1.2"

# README.md required by poetry install
COPY pyproject.toml poetry.lock run.py manifest.json README.md $FLYWHEEL/
COPY fw_gear_file_curator $FLYWHEEL/fw_gear_file_curator

RUN poetry install --no-dev

# Configure entrypoint
RUN chmod a+x $FLYWHEEL/run.py
ENTRYPOINT ["poetry","run","python","/flywheel/v0/run.py"]
