import os

ACTIVE_ENV = os.environ.get("ACTIVE_ENV", "dev")

TEST_USER_EMAIL = "e2etmg+02@hotmail.com"
TEST_USER_PASSWORD = "123456"
EMAIL_FROM = "bsit833@gmail.com"
IMAP_HOST = "outlook.office365.com"
IMAP_PORT = 993
EMAIL_ACCOUNT_USERNAME = "e2etmg@hotmail.com"
EMAIL_ACCOUNT_PASSWORD = "fbb06fc8-fd64-11ee-8a70-d73cbe5bfd61"

STORE_CONFIG = {
    "dev": {"url": "https://quickstart-a91e1214.myshopify.com", "password": "test123", "require_store_password": True},
    "stg": {"url": "https://tmg-staging.myshopify.com", "password": "test123", "require_store_password": True},
}

STORE_URL = STORE_CONFIG.get(ACTIVE_ENV).get("url")
REQUIRE_STORE_PASSWORD = STORE_CONFIG.get(ACTIVE_ENV).get("require_store_password")
STORE_PASSWORD = STORE_CONFIG.get(ACTIVE_ENV).get("password")

API_PARAMS = {
    "dev": {
        "url": "https://api.dev.tmgcorp.net",
        "hmac": {
            "logged_in_customer_id": "7061007532163",
            "path_prefix": "/apps/dev",
            "shop": "quickstart-a91e1214.myshopify.com",
            "signature": "9e655406dc5d9cedb399ecae73c642a5cc7410a5a083fc4fb8d250ec56922476",
            "timestamp": "1713866190",
        },
    },
    "stg": {
        "url": "https://api.stg.tmgcorp.net",
        "hmac": {
            "logged_in_customer_id": "6519862853674",
            "path_prefix": "/apps/prod",
            "shop": "themodern-groom.myshopify.com",
            "signature": "945b5cc30592e6d967717cee1a66da445d2ac6222971cfe645d72268ca66b8d3",
            "timestamp": "1713351981",
        },
    },
}

API_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}
