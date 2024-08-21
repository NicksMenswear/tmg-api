import os


class Config:
    STAGE = os.getenv("STAGE", "dev")
    API_TOKEN = os.getenv("API_TOKEN", "123")
    API_ENDPOINT_URL = f"https://api.{STAGE}.tmgcorp.net"
    NUM_WEEKS_ALLOWED_FOR_FREE_SHIPPING = 6
    TMG_APP_TESTING = False
    EXPEDITED_SHIPPING_VARIANT_ID = os.getenv("expedited_shipping_variant_id", "44714760372355")


class TestConfig(Config):
    STAGE = "test"
    TMG_APP_TESTING = True
