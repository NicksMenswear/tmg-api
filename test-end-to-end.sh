#!/usr/bin/env bash

export ACTIVE_ENV=${ACTIVE_ENV:-stg}

echo "Running e2e against '${ACTIVE_ENV}' environment."

docker-compose up --build --abort-on-container-exit test-end-to-end
