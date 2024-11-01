#!/usr/bin/env bash

export ACTIVE_ENV=${ACTIVE_ENV:-dev}
export BROWSER=${BROWSER:-chromium}
export TEST_GROUP=${TEST_GROUP:-all}
export SHOPIFY_STORE_HOST=${SHOPIFY_STORE_HOST:-"quickstart-a91e1214.myshopify.com"}
export SHOPIFY_ADMIN_API_ACCESS_TOKEN=${SHOPIFY_ADMIN_API_ACCESS_TOKEN:-"shpat_1234567890abcdef"}

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
echo "Shopify host: ${SHOPIFY_STORE_HOST}"

if [ "$TEST_GROUP" == "all" ]; then
  docker-compose up --build --abort-on-container-exit test-e2e
else
  docker-compose up --build --abort-on-container-exit test-e2e-${TEST_GROUP}
fi
