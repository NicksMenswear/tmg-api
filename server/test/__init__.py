from flask_testing import TestCase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.app import init_app
from server.test.services.emails import FakeEmailService
from server.test.services.shopify import FakeShopifyService

engine = create_engine(f"postgresql://postgres:postgres@localhost:5432/tmg_api")


class BaseTestCase(TestCase):
    def create_app(self):
        app = init_app(swagger=False).app
        app.config["TESTING"] = True
        app.shopify_service = FakeShopifyService()
        app.email_service = FakeEmailService()
        self.session = sessionmaker(bind=engine)
        return app

    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.hmac_query_params = {
            "logged_in_customer_id": "123456789",
            "shop": "test",
            "path_prefix": "/",
            "timestamp": "1712665883",
            "signature": "test",
        }
