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

response=$(curl https://api."${STAGE}".tmgcorp.net/jobs/system/e2e-clean-up --silent \
  -H "Content-Type: application/json" \
  -H "X-API-ACCESS-TOKEN: ${X_API_ACCESS_TOKEN}")

echo "$response" | jq -c '.[]' | while read -r item; do
  id=$(echo "$item" | jq -r '.id')
  email=$(echo "$item" | jq -r '.email')

  curl https://api."${STAGE}".tmgcorp.net/jobs/system/e2e-clean-up --silent \
    -X POST \
    -H "Content-Type: application/json" \
    -H "X-API-ACCESS-TOKEN: ${X_API_ACCESS_TOKEN}" \
    -d "{\"id\": \"$id\", \"email\": \"$email\"}" \
    --max-time 300
done
