ARG BASE

FROM ${BASE}

ENV FLYWHEEL="/flywheel/v0"

COPY tests ${FLYWHEEL}/tests
COPY .pre-commit-config.yaml ${FLYWHEEL}/
COPY .git ${FLYWHEEL}/.git

# Installing pre-commit
RUN pip install pre-commit
RUN pre-commit install

# Need to install poetry with dev dependencies
RUN poetry install

ENTRYPOINT [""]
