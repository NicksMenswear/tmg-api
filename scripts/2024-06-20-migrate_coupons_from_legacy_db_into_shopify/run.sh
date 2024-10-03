#!/usr/bin/env bash

if [ -z "$LEGACY_DB_PASSWORD" ]; then
  echo "LEGACY_DB_PASSWORD env variable is not set. Please set it before running this script."
  exit 1
fi

if [ -z "$SHOPIFY_ADMIN_API_ACCESS_TOKEN" ]; then
  echo "SHOPIFY_ADMIN_API_ACCESS_TOKEN env variable is not set. Please set it before running this script."
  exit 1
fi

export SHOPIFY_STORE_NAME=${SHOPIFY_STORE_NAME:-quickstart-a91e1214}

python scripts/migrate_coupons_from_legacy_db_into_shopify/main.py