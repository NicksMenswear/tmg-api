#!/usr/bin/env bash

export ACTIVE_ENV=${ACTIVE_ENV:-stg}
export BROWSER=${BROWSER:-webkit}

echo "Running e2e against '${ACTIVE_ENV}' environment in '${BROWSER}' browser."

docker-compose up --build --abort-on-container-exit test-end-to-end
