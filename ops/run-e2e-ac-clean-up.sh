#!/bin/bash

set -ex

if [ -z "$STAGE" ]; then
  echo "STAGE env variable is not set"
  exit 1
fi

if [ -z "$X_API_ACCESS_TOKEN" ]; then
  echo "X_API_ACCESS_TOKEN env variable is not set"
  exit 1
fi

curl https://api."${STAGE}".tmgcorp.net/jobs/system/e2e-ac-clean-up \
  -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-ACCESS-TOKEN: ${X_API_ACCESS_TOKEN}" \
  -d '{}' \
  --max-time 300
