#!/usr/bin/env bash

required_vars=(
  "LEGACY_DB_PASSWORD"
  "NEW_DB_PASSWORD"
  "NEW_DB_USER"
  "NEW_DB_NAME"
  "SHOPIFY_ADMIN_API_ACCESS_TOKEN"
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "$var env variable is not set. Please set it before running this script."
    exit 1
  fi
done

export SHOPIFY_STORE_NAME=${SHOPIFY_STORE_NAME:-quickstart-a91e1214}

python scripts/migrate_users_from_legacy_db_into_shopify/main.py