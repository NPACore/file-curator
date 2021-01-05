ARG BASE

FROM ${BASE}

ENV FLYWHEEL="/flywheel/v0"

# To install poetry dev dependencies
RUN poetry install

COPY tests ./tests

ENTRYPOINT [""]
