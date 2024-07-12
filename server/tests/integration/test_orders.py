from __future__ import absolute_import

import uuid
from datetime import timedelta, datetime

from server.database.database_manager import db
from server.database.models import Order
from server.services.order import (
    ORDER_STATUS_PENDING_MEASUREMENTS,
    ORDER_STATUS_PENDING_MISSING_SKU,
    ORDER_STATUS_READY,
)
from server.services.sku_builder import ProductType
from server.tests.integration import BaseTestCase, fixtures


class TestOrders(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_get_pending_orders_no_orders_for_all_users(self):
        # when
        orders = self.order_service.get_orders_by_status_and_not_older_then_days(ORDER_STATUS_PENDING_MEASUREMENTS, 10)

        # then
        self.assertEqual(0, len(orders))

    def test_get_pending_orders_no_orders_for_single_user(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        orders = self.order_service.get_orders_by_status_and_not_older_then_days(
            ORDER_STATUS_PENDING_MEASUREMENTS, 10, user.id
        )

        # then
        self.assertEqual(0, len(orders))

    def test_get_pending_orders_from_mix_of_orders_for_all_users(self):
        # given
        user1 = self.user_service.create_user(fixtures.create_user_request())
        user2 = self.user_service.create_user(fixtures.create_user_request())
        order1 = self.order_service.create_order(
            fixtures.create_order_request(user_id=user1.id, status=ORDER_STATUS_PENDING_MISSING_SKU)
        )
        order2 = self.order_service.create_order(
            fixtures.create_order_request(user_id=user2.id, status=ORDER_STATUS_PENDING_MEASUREMENTS)
        )
        order3 = self.order_service.create_order(
            fixtures.create_order_request(user_id=user2.id, status=ORDER_STATUS_READY)
        )

        # when
        orders = self.order_service.get_orders_by_status_and_not_older_then_days(ORDER_STATUS_PENDING_MEASUREMENTS, 10)

        # then
        self.assertEqual(1, len(orders))
        pending_order = orders[0]
        self.assertEqual(order2.id, pending_order.id)
        self.assertEqual(order2.status, pending_order.status)

    def test_get_pending_orders_from_mix_of_orders_for_single_user(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        order1 = self.order_service.create_order(
            fixtures.create_order_request(user_id=user.id, status=ORDER_STATUS_PENDING_MISSING_SKU)
        )
        order2 = self.order_service.create_order(
            fixtures.create_order_request(user_id=user.id, status=ORDER_STATUS_PENDING_MEASUREMENTS)
        )
        order3 = self.order_service.create_order(
            fixtures.create_order_request(user_id=user.id, status=ORDER_STATUS_READY)
        )

        # when
        orders = self.order_service.get_orders_by_status_and_not_older_then_days(ORDER_STATUS_PENDING_MEASUREMENTS, 10)

        # then
        self.assertEqual(1, len(orders))
        pending_order = orders[0]
        self.assertEqual(order2.id, pending_order.id)
        self.assertEqual(order2.status, pending_order.status)

    def test_get_pending_orders_excluded_too_old_for_user(self):
        # given
        max_days = 10
        user = self.user_service.create_user(fixtures.create_user_request())
        order1 = self.order_service.create_order(
            fixtures.create_order_request(user_id=user.id, status=ORDER_STATUS_PENDING_MEASUREMENTS)
        )
        order2 = self.order_service.create_order(
            fixtures.create_order_request(user_id=user.id, status=ORDER_STATUS_PENDING_MEASUREMENTS)
        )
        # update in db directly
        db_order1 = Order.query.filter(Order.id == order1.id).first()
        db_order1.created_at = datetime.utcnow() - timedelta(days=max_days + 5)
        db.session.commit()

        # when
        orders1 = self.order_service.get_orders_by_status_and_not_older_then_days(
            ORDER_STATUS_PENDING_MEASUREMENTS, max_days
        )
        orders2 = self.order_service.get_orders_by_status_and_not_older_then_days(
            ORDER_STATUS_PENDING_MEASUREMENTS, max_days + 100
        )

        # then
        self.assertEqual(1, len(orders1))
        pending_order = orders1[0]
        self.assertEqual(order2.id, pending_order.id)
        self.assertEqual(order2.status, pending_order.status)
        self.assertEqual(2, len(orders2))

    def test_update_order_skus_according_to_measurements_for_order_without_products(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        size_model = self.size_service.create_size(fixtures.store_size_request(user_id=user.id))
        measurement_model = self.measurement_service.create_measurement(
            fixtures.store_measurement_request(user_id=user.id)
        )
        order = self.order_service.create_order(
            fixtures.create_order_request(user_id=user.id, status=ORDER_STATUS_PENDING_MEASUREMENTS)
        )

        # when
        updated_order = self.order_service.update_order_skus_according_to_measurements(
            order, size_model, measurement_model
        )

        # then
        self.assertEqual(order, updated_order)

    def test_update_order_status_if_shopify_sku_is_missing_but_measurements_provided(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        size_model = self.size_service.create_size(fixtures.store_size_request(user_id=user.id))
        measurement_model = self.measurement_service.create_measurement(
            fixtures.store_measurement_request(user_id=user.id)
        )
        order = self.order_service.create_order(
            fixtures.create_order_request(
                user_id=user.id,
                status=ORDER_STATUS_PENDING_MEASUREMENTS,
                products=[fixtures.create_product_request(shopify_sku=None)],
            )
        )

        # when
        updated_order = self.order_service.update_order_skus_according_to_measurements(
            order, size_model, measurement_model
        )

        # then
        self.assertEqual(updated_order.status, ORDER_STATUS_PENDING_MISSING_SKU)

    def test_update_order_status_if_shopify_sku_is_provided_by_invalid(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        size_model = self.size_service.create_size(fixtures.store_size_request(user_id=user.id))
        measurement_model = self.measurement_service.create_measurement(
            fixtures.store_measurement_request(user_id=user.id)
        )
        order = self.order_service.create_order(
            fixtures.create_order_request(
                user_id=user.id,
                status=ORDER_STATUS_PENDING_MEASUREMENTS,
                products=[fixtures.create_product_request(shopify_sku=f"z-{uuid.uuid4()}")],
            )
        )

        # when
        updated_order = self.order_service.update_order_skus_according_to_measurements(
            order, size_model, measurement_model
        )

        # then
        self.assertEqual(updated_order.status, ORDER_STATUS_PENDING_MISSING_SKU)

    def test_update_order_status_if_product_doesnt_require_measurements(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        size_model = self.size_service.create_size(fixtures.store_size_request(user_id=user.id))
        measurement_model = self.measurement_service.create_measurement(
            fixtures.store_measurement_request(user_id=user.id)
        )
        order = self.order_service.create_order(
            fixtures.create_order_request(
                user_id=user.id,
                status=ORDER_STATUS_PENDING_MEASUREMENTS,
                products=[
                    fixtures.create_product_request(
                        shopify_sku=self.get_random_shopify_sku_by_product_type(ProductType.BOW_TIE)
                    )
                ],
            )
        )

        # when
        self.assertIsNone(order.products[0].sku)

        updated_order = self.order_service.update_order_skus_according_to_measurements(
            order, size_model, measurement_model
        )

        # then
        self.assertEqual(updated_order.status, ORDER_STATUS_READY)
        self.assertIsNotNone(self.order_service.get_product_by_id(order.products[0].id).sku)

    def test_update_order_status_if_product_requires_measurements(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        size_model = self.size_service.create_size(fixtures.store_size_request(user_id=user.id))
        measurement_model = self.measurement_service.create_measurement(
            fixtures.store_measurement_request(user_id=user.id)
        )
        order = self.order_service.create_order(
            fixtures.create_order_request(
                user_id=user.id,
                status=ORDER_STATUS_PENDING_MEASUREMENTS,
                products=[
                    fixtures.create_product_request(
                        shopify_sku=self.get_random_shopify_sku_by_product_type(ProductType.PANTS)
                    )
                ],
            )
        )

        # when
        self.assertIsNone(order.products[0].sku)

        updated_order = self.order_service.update_order_skus_according_to_measurements(
            order, size_model, measurement_model
        )

        # then
        self.assertEqual(updated_order.status, ORDER_STATUS_READY)
        self.assertIsNotNone(self.order_service.get_product_by_id(order.products[0].id).sku)
