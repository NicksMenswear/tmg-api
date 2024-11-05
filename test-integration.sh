#!/usr/bin/env bash

export BROWSER=${BROWSER:-chromium}
export VIEWPORT=${VIEWPORT:-"mobile"}
export SHOPIFY_STORE=${SHOPIFY_STORE:-"quickstart-a91e1214"}
export SHOPIFY_ADMIN_API_ACCESS_TOKEN=${SHOPIFY_ADMIN_API_ACCESS_TOKEN:-"shpat_1234567890abcdef"}

docker-compose up --build --abort-on-container-exit test-integration
