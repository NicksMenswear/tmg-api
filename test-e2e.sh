#!/usr/bin/env bash

export ACTIVE_ENV=${ACTIVE_ENV:-dev}
export BROWSER=${BROWSER:-chromium}
export TEST_GROUP=${TEST_GROUP:-all}
export VIEWPORT=${VIEWPORT:-1280x720}

# Usage
#   # Run all tests:
#   ./test-e2e.sh
#
#   # Run tests in a specific group:
#   ./test-e2e.sh <group-N>
#
#   # for example:
#   ./test-e2e.sh group-1

echo "Running e2e against '${ACTIVE_ENV}' environment in '${BROWSER}' browser."

if [ "$TEST_GROUP" == "all" ]; then
  docker-compose up --build --abort-on-container-exit test-e2e
else
  docker-compose up --build --abort-on-container-exit test-e2e-${TEST_GROUP}
fi
