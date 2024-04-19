import os

from flask_testing import TestCase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.app import init_app
from server.database.models import Order, ProductItem, User, Event, Look, Role, Attendee, OrderItem, Cart, CartProduct
from server.services.emails import FakeEmailService
from server.services.shopify import FakeShopifyService

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(DATABASE_URL)

CONTENT_TYPE_JSON = "application/json"


class BaseTestCase(TestCase):
    def create_app(self):
        app = init_app().app
        app.config["TESTING"] = True
        app.shopify_service = FakeShopifyService()
        app.email_service = FakeEmailService()
        self.session = sessionmaker(bind=engine)
        return app

    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.session_factory = self.session
        self.db = self.session_factory()

        self.db.query(CartProduct).delete()
        self.db.query(Cart).delete()
        self.db.query(Attendee).delete()
        self.db.query(Role).delete()
        self.db.query(Look).delete()
        self.db.query(OrderItem).delete()
        self.db.query(Order).delete()
        self.db.query(ProductItem).delete()
        self.db.query(Event).delete()
        self.db.query(User).delete()
        self.db.commit()

        self.content_type = CONTENT_TYPE_JSON
        self.request_headers = {
            "Accept": CONTENT_TYPE_JSON,
        }

        self.hmac_query_params = {
            "logged_in_customer_id": "123456789",
            "shop": "test",
            "path_prefix": "/",
            "timestamp": "1712665883",
            "signature": "test",
        }

    def assert_equal_left(self, left, right):
        # Asserts that all key-value pairs in left are present and equal in right.
        for key in left:
            self.assertEqual(left[key], right[key])
