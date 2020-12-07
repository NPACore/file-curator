ARG BASE

FROM ${BASE}

COPY tests/ ${FLYWHEEL}/tests

RUN python3 -m pip install --user -r tests/requirements.txt
# Configure entrypoint
ENTRYPOINT []
