FROM flywheel/python:3.12-alpine as base

ENV FLYWHEEL="/flywheel/v0"
WORKDIR ${FLYWHEEL}

# Installing main dependencies
COPY requirements.txt $FLYWHEEL/
RUN uv pip install --no-cache-dir -r $FLYWHEEL/requirements.txt

# Installing the current project (most likely to change, above layer can be cached)
COPY . $FLYWHEEL/
RUN pip install --no-cache-dir .
RUN chmod a+x $FLYWHEEL/run.py

FROM base as dev

RUN uv pip install --no-cache-dir -r $FLYWHEEL/requirements-dev.txt


FROM base as prod
# Configure entrypoint
ENTRYPOINT ["python","/flywheel/v0/run.py"]
