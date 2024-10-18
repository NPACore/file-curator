FROM flywheel/python:3.12-alpine as base
ENV FLYWHEEL=/flywheel/v0
WORKDIR $FLYWHEEL
ENTRYPOINT ["python", "/flywheel/v0/run.py"]
COPY requirements.txt .
RUN uv pip install -rrequirements.txt

FROM base as dev
COPY requirements-dev.txt .
RUN uv pip install -rrequirements-dev.txt
COPY . .
RUN uv pip install --no-deps -e.

FROM base as prod
COPY . .
RUN uv pip install --no-deps -e.
