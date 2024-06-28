from flask_testing import TestCase

from server.app import init_app, init_db
from server.database.database_manager import db
from server.database.models import (
    Order,
    ProductItem,
    User,
    Event,
    Look,
    Role,
    Attendee,
    OrderItem,
    Discount,
    Product,
    Size,
    Measurement,
)
from server.flask_app import FlaskApp

CONTENT_TYPE_JSON = "application/json"


class BaseTestCase(TestCase):
    def create_app(self):
        FlaskApp.cleanup()
        app = init_app(True).app
        init_db()
        return app

    def setUp(self):
        super(BaseTestCase, self).setUp()

        Discount.query.delete()
        Attendee.query.delete()
        Role.query.delete()
        Look.query.delete()
        OrderItem.query.delete()
        Order.query.delete()
        Product.query.delete()
        Event.query.delete()
        User.query.delete()
        Size.query.delete()
        Measurement.query.delete()
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

        self.user_service = self.app.user_service
        self.role_service = self.app.role_service
        self.look_service = self.app.look_service
        self.event_service = self.app.event_service
        self.order_service = self.app.order_service
        self.attendee_service = self.app.attendee_service
        self.discount_service = self.app.discount_service
        self.webhook_service = self.app.webhook_service
        self.size_service = self.app.size_service
