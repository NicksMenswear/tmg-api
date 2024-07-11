import random

from flask_testing import TestCase

from server.app import init_app, init_db
from server.database.database_manager import db
from server.database.models import (
    Order,
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
from server.models.shopify_model import ShopifyVariantModel
from server.services.shopify import FakeShopifyService

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
        Size.query.delete()
        Measurement.query.delete()
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

        self.user_service = self.app.user_service
        self.role_service = self.app.role_service
        self.look_service = self.app.look_service
        self.event_service = self.app.event_service
        self.order_service = self.app.order_service
        self.attendee_service = self.app.attendee_service
        self.discount_service = self.app.discount_service
        self.webhook_service = self.app.webhook_service
        self.shopify_service = self.app.shopify_service
        self.size_service = self.app.size_service
        self.measurement_service = self.app.measurement_service

    def populate_shopify_variants(self, num_variants=100):
        if not isinstance(self.shopify_service, FakeShopifyService):
            return

        for _ in range(num_variants):
            variant_id = str(random.randint(1000000, 100000000))

            self.shopify_service.shopify_variants[variant_id] = ShopifyVariantModel(
                **{
                    "product_id": str(random.randint(10000, 1000000)),
                    "product_title": f"Product for variant {variant_id}",
                    "variant_id": variant_id,
                    "variant_title": f"Variant {variant_id}",
                    "variant_sku": f"00{random.randint(10000, 1000000)}",
                    "variant_price": random.randint(100, 1000),
                }
            )

    def get_random_shopify_variant(self):
        if not isinstance(self.shopify_service, FakeShopifyService):
            return None

        keys = list(self.shopify_service.shopify_variants.keys())
        random_key = keys[random.randint(0, len(keys) - 1)]

        return self.shopify_service.shopify_variants[random_key]

    def create_look_test_product_specs(self, num_variants=5):
        suit_variant = self.get_random_shopify_variant()

        variants = [suit_variant.variant_id]

        for _ in range(num_variants):
            variants.append(self.get_random_shopify_variant().variant_id)

        return {
            "suit_variant": suit_variant.variant_id,
            "variants": variants,
        }
