# USAGE

Before running script figure out 4 env variables
- `SHOPIFY_STORE_NAME` (e.g. `quickstart-a91e1214`)
- `SHOPIFY_ADMIN_API_ACCESS_TOKEN` (e.g. `shpat_1234567890abcdef1234567890abcdef`)
- `LEGACY_DB_PASSWORD`
- `NEW_DB_NAME`
- `NEW_DB_HOST`
- `NEW_DB_USER`

Then run the script from repo root directory with the following command:

```sh
SHOPIFY_STORE_NAME=quickstart-a91e1214 \
SHOPIFY_ADMIN_API_ACCESS=shpat_1234567890abcdef1234567890abcdef \
LEGACY_DB_PASSWORD=your_password_here \
NEW_DB_PASSWORD=your_password_here \
NEW_DB_HOST=your_host_here \
NEW_DB_USER=your_user_here \
./scripts/migrate_users_from_legacy_db_into_shopify/run.sh
```