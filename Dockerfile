FROM flywheel/python-gdcm:sse AS base
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]
ENV FLYWHEEL="/flywheel/v0"
WORKDIR $FLYWHEEL
ENTRYPOINT ["python", "/flywheel/v0/run.py"]

FROM base AS build
RUN apk --no-cache add -tbuild-deps build-base cargo cmake linux-headers
# RUN apk upgrade --no-cache && apk --no-cache add gcc g++ musl-dev linux-headers python3-dev
COPY requirements.txt ./
RUN uv pip install -rrequirements.txt

FROM build AS dev
COPY requirements-dev.txt ./
RUN uv pip install -rrequirements-dev.txt
COPY . .
RUN uv pip install --no-deps -e.

FROM base
COPY --from=build /venv /venv
COPY . .
RUN uv pip install --no-deps -e.
