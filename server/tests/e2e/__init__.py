import os
import traceback
from functools import wraps
from typing import Callable, Set

from playwright.sync_api import Page

ACTIVE_ENV = os.environ.get("ACTIVE_ENV", "dev")

TEST_USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "e2e+02@mail.dev.tmgcorp.net")
TEST_USER_PASSWORD = "123456"
EMAIL_FROM = "info@themoderngroom.com"
IMAP_HOST = "mail.dev.tmgcorp.net"
IMAP_PORT = 993
EMAIL_ACCOUNT_USERNAME = "e2e"
EMAIL_ACCOUNT_PASSWORD = "e5948b3e-50b1-11ef-88d6-478eb041eda8"
EMAIL_SUBJECT_EVENT_INVITATION = "The Modern Groom: Event Invitation"
EMAIL_SUBJECT_ACCOUNT_CREATED = "The Modern Groom: Account Created"
EMAIL_SUBJECT_CUSTOMER_ACCOUNT_CONFIRMATION = "Customer account confirmation"
DEFAULT_EVENT_DATE = "2028-04-18"
DEFAULT_EVENT_PRETTY_DATE = "Tuesday, April 18, 2028"
TEST_COUPON_DISCOUNT_CODE = "E2E-1$-OFF"

STORE_CONFIG = {
    "dev": {"url": "https://quickstart-a91e1214.myshopify.com", "password": "test123", "require_store_password": True},
    "stg": {"url": "https://tmg-staging.myshopify.com", "password": "test123", "require_store_password": True},
    "prd": {
        "url": "https://themoderngroom.com",
        "password": "test123",
        "require_store_password": False,
        "has_additional_initial_screen_on_store_access": False,
    },
}

STORE_URL = STORE_CONFIG.get(ACTIVE_ENV).get("url")
REQUIRE_STORE_PASSWORD = STORE_CONFIG.get(ACTIVE_ENV).get("require_store_password")
HAS_ADDITIONAL_INITIAL_SCREEN_ON_STORE_ACCESS = STORE_CONFIG.get(ACTIVE_ENV).get(
    "has_additional_initial_screen_on_store_access", False
)
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
            "logged_in_customer_id": "7304856600801",
            "path_prefix": "/apps/staging",
            "shop": "tmg-staging.myshopify.com",
            "signature": "ddca24b84f084aad360f8530f071a53c9948b14f6671b0184479cf277a5120b8",
            "timestamp": "1713979125",
        },
    },
    "prd": {
        "url": "https://api.prd.tmgcorp.net",
        "hmac": {
            "logged_in_customer_id": "6680352456746",
            "path_prefix": "/apps/prd",
            "shop": "themodern-groom.myshopify.com",
            "signature": "d876ab9a5505497002ad038050b8ec484abf807d2f5221066e32ce67a4e34fb1",
            "timestamp": "1718364754",
        },
    },
}

API_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def e2e_error_handling(func):
    @wraps(func)
    def wrapper(page: Page, *args, **kwargs):
        try:
            return func(page, *args, **kwargs)
        except Exception as e:
            print("An error occurred: ============================================\n", e)
            print("Traceback: ============================================\n", traceback.format_exc())
            print("Current URL: ============================================\n", page.url)
            # print("HTML Content: ============================================\n", page.content())
            raise

    return wrapper


def e2e_allowed_in(allowed_envs: Set[str]) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            active_env = os.getenv("ACTIVE_ENV", "dev")

            if active_env in allowed_envs:
                return func(*args, **kwargs)
            else:
                print(
                    f"Function {func.__name__} not executed because ACTIVE_ENV is '{active_env}', which is not in {allowed_envs}."
                )
                return None

        return wrapper

    return decorator
