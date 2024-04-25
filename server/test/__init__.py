from flask_testing import TestCase

from server.app import init_app, init_db
from server.flask_app import FlaskApp
from server.database.database_manager import db
from server.database.models import Order, ProductItem, User, Event, Look, Role, Attendee, OrderItem, Cart, CartProduct
from server.services.emails import FakeEmailService
from server.services.shopify import FakeShopifyService

CONTENT_TYPE_JSON = "application/json"


class BaseTestCase(TestCase):
    def create_app(self):
        FlaskApp.cleanup()
        app = init_app().app
        init_db()
        app.config["TMG_APP_TESTING"] = True
        app.shopify_service = FakeShopifyService()
        app.email_service = FakeEmailService()
        return app

    def setUp(self):
        super(BaseTestCase, self).setUp()

        CartProduct.query.delete()
        Cart.query.delete()
        Attendee.query.delete()
        Role.query.delete()
        Look.query.delete()
        OrderItem.query.delete()
        Order.query.delete()
        ProductItem.query.delete()
        Event.query.delete()
        User.query.delete()
        db.session.commit()

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
