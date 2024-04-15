from __future__ import absolute_import

import json
import uuid
from datetime import datetime

from server import encoder
from server.database.models import Order
from server.services.event import EventService
from server.services.order import OrderService
from server.services.product import ProductService
from server.services.user import UserService
from server.test import BaseTestCase, fixtures


class TestOrders(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.user_service = UserService(self.session_factory)
        self.event_service = EventService(self.session_factory)
        self.order_service = OrderService(self.session_factory)
        self.product_service = ProductService(self.session_factory)

    def assert_equal_response_order_with_db_order(self, order: Order, response_order: dict):
        self.assertEqual(response_order["id"], str(order["id"]))
        self.assertEqual(response_order["user_id"], str(order["user_id"]))
        self.assertEqual(response_order["event_id"], str(order["event_id"]))
        self.assertEqual(response_order["shipped_date"], order["shipped_date"])
        self.assertEqual(response_order["received_date"], order["received_date"])

    def test_get_non_existing_order_by_id(self):
        # when
        response = self.client.open(
            "/orders/{order_id}".format(order_id=str(uuid.uuid4())),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_get_order_by_id(self):
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        product = self.product_service.create_product(**fixtures.product_request())
        order = self.order_service.create_order(
            **fixtures.order_request(
                email=user.email,
                user_id=user.id,
                event_id=event.id,
                items=[
                    {"name": product.name, "quantity": 1},
                ],
            )
        )

        # when
        response = self.client.open(
            "/orders/{order_id}".format(order_id=str(order["id"])),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
        )

        # then
        self.assert200(response)

    def test_create_order_for_invalid_user(self):
        # given
        order = fixtures.order_request(email=f"{str(uuid.uuid4())}@example.com")

        # when
        response = self.client.open(
            "/orders",
            method="POST",
            query_string=self.hmac_query_params,
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(order, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 404)

    def test_create_order_for_invalid_event(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        order = fixtures.order_request(email=user.email)

        # when
        response = self.client.open(
            "/orders",
            method="POST",
            query_string=self.hmac_query_params,
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(order, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 404)

    def test_create_order_without_items(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))

        # when
        response = self.client.open(
            "/orders",
            method="POST",
            query_string=self.hmac_query_params,
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(fixtures.order_request(email=user.email), cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 201)
        order = self.order_service.get_order_by_id(response.json["id"])
        self.assert_equal_response_order_with_db_order(order, response.json)
        items = self.order_service.get_order_items_by_order_id(order["id"])
        self.assertEqual(0, len(items))

    def test_create_order(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        product1 = self.product_service.create_product(**fixtures.product_request())
        product2 = self.product_service.create_product(**fixtures.product_request())

        # when
        order_request = fixtures.order_request(
            email=user.email,
            items=[
                {"name": product1.name, "quantity": 1},
                {"name": product2.name, "quantity": 2},
            ],
        )

        response = self.client.open(
            "/orders",
            method="POST",
            query_string=self.hmac_query_params,
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(order_request, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 201)
        order = self.order_service.get_order_by_id(response.json["id"])
        self.assert_equal_response_order_with_db_order(order, response.json)
        items = self.order_service.get_order_items_by_order_id(order["id"])
        self.assertEqual(2, len(items))
        self.assertEqual(product1.id, items[0].product_id)
        self.assertEqual(1, items[0].quantity)
        self.assertEqual(product2.id, items[1].product_id)
        self.assertEqual(2, items[1].quantity)

    def test_get_orders_empty(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))

        # when
        query_params = {
            **self.hmac_query_params,
            "user_id": str(user.id),
            "event_id": str(event.id),
        }

        response = self.client.open(
            "/orders",
            method="GET",
            query_string=query_params,
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_orders(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        product1 = self.product_service.create_product(**fixtures.product_request())
        product2 = self.product_service.create_product(**fixtures.product_request())
        product3 = self.product_service.create_product(**fixtures.product_request())
        order1 = self.order_service.create_order(
            **fixtures.order_request(
                email=user.email,
                user_id=user.id,
                event_id=event.id,
                items=[
                    {"name": product1.name, "quantity": 1},
                    {"name": product2.name, "quantity": 2},
                ],
            )
        )
        order2 = self.order_service.create_order(
            **fixtures.order_request(
                email=user.email,
                user_id=user.id,
                event_id=event.id,
                items=[
                    {"name": product3.name, "quantity": 3},
                ],
            )
        )

        # when
        query_params = {
            **self.hmac_query_params,
            "user_id": str(user.id),
            "event_id": str(event.id),
        }

        response = self.client.open(
            "/orders",
            method="GET",
            query_string=query_params,
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)

    def test_update_order(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        product = self.product_service.create_product(**fixtures.product_request())
        order = self.order_service.create_order(
            **fixtures.order_request(
                email=user.email,
                user_id=user.id,
                event_id=event.id,
                items=[
                    {"name": product.name, "quantity": 1},
                ],
            )
        )

        # when
        response = self.client.open(
            "/orders",
            method="PUT",
            query_string=self.hmac_query_params,
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.update_order_request(
                    id=order["id"], shipped_date=datetime.now().isoformat(), received_date=datetime.now().isoformat()
                ),
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 200)

    def test_delete_order(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        product = self.product_service.create_product(**fixtures.product_request())
        order = self.order_service.create_order(
            **fixtures.order_request(
                email=user.email,
                user_id=user.id,
                event_id=event.id,
                items=[
                    {"name": product.name, "quantity": 1},
                ],
            )
        )

        # when
        query_params = {
            **self.hmac_query_params,
            "order_id": order["id"],
        }

        response = self.client.open(
            "/orders",
            method="DELETE",
            query_string=query_params,
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 204)
        self.assertIsNone(self.order_service.get_order_by_id(order["id"]))
        self.assertEqual(0, len(self.order_service.get_order_items_by_order_id(order["id"])))

    def test_delete_order_not_found(self):
        # when
        response = self.client.open(
            "/orders",
            method="DELETE",
            query_string={
                **self.hmac_query_params,
                "order_id": str(uuid.uuid4()),
            },
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)
