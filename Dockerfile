FROM python:3.8 as builder
RUN sh -c "$(curl -ssL https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin
WORKDIR /app/
COPY pyproject.toml poetry.lock /app/
RUN pip install poetry
RUN poetry config virtualenvs.create false && poetry install --no-interaction
COPY . /app/
RUN task build

FROM ubuntu:20.04
RUN apt-get update && apt-get install -y git && \
  rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/dist/dht /usr/local/bin/dht
ENTRYPOINT ["/usr/local/bin/dht"]
