from __future__ import absolute_import

import json
import unittest
import uuid

from server import encoder
from server.database.models import Cart, CartProduct
from server.services.attendee import AttendeeService
from server.services.event import EventService
from server.services.legacy.cart import CartService
from server.services.look import LookService
from server.services.role import RoleService
from server.services.user import UserService
from server.test import BaseTestCase, fixtures


@unittest.skip("Carts are not used at the moment.")
class TestCarts(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.look_service = LookService()
        self.role_service = RoleService()
        self.user_service = UserService()
        self.attendee_service = AttendeeService()
        self.event_service = EventService()
        self.cart_service = CartService()

    def assert_equal_cart(self, cart: Cart, request_cart: dict):
        self.assertEqual(request_cart.get("user_id"), str(cart.user_id) if cart.user_id else None)
        self.assertEqual(request_cart.get("event_id"), str(cart.event_id))
        self.assertEqual(request_cart.get("attendee_id"), str(cart.attendee_id))

    def assert_equal_cart_product(self, cart_product: CartProduct, request_cart_product: dict):
        self.assertEqual(request_cart_product["product_id"], cart_product.product_id)
        self.assertEqual(request_cart_product["variation_id"], cart_product.variation_id)
        self.assertEqual(request_cart_product["category"], cart_product.category)
        self.assertEqual(request_cart_product["quantity"], cart_product.quantity)

    def test_create_cart_without_user_and_without_products(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(fixtures.create_look_request(user_id=str(user.id)))
        role = self.role_service.create_role(fixtures.role_request(event_id=str(event.id)))
        attendee = self.attendee_service.create_attendee(
            fixtures.attendee_request(email=user.email, event_id=str(event.id), role=str(role.id), look_id=str(look.id))
        )

        # when
        cart_request = fixtures.create_cart_request(event_id=str(event.id), attendee_id=str(attendee.id))
        del cart_request["user_id"]

        response = self.client.open(
            "/carts",
            query_string=self.hmac_query_params,
            data=json.dumps(cart_request, cls=encoder.CustomJSONEncoder),
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        cart_id = response.json
        self.assertIsNotNone(cart_id)
        cart = Cart.query.filter_by(id=cart_id).one_or_none()
        self.assert_equal_cart(cart, cart_request)
        self.assertEqual(cart.cart_products.count(), 0)

    def test_create_cart_with_user(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(fixtures.create_look_request(user_id=str(user.id)))
        role = self.role_service.create_role(fixtures.role_request(event_id=str(event.id)))
        attendee = self.attendee_service.create_attendee(
            fixtures.attendee_request(email=user.email, event_id=str(event.id), role=str(role.id), look_id=str(look.id))
        )

        # when
        cart_request = fixtures.create_cart_request(
            user_id=str(user.id), event_id=str(event.id), attendee_id=str(attendee.id)
        )

        response = self.client.open(
            "/carts",
            query_string=self.hmac_query_params,
            data=json.dumps(cart_request, cls=encoder.CustomJSONEncoder),
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        cart_id = response.json
        self.assertIsNotNone(cart_id)
        cart = Cart.query.filter_by(id=cart_id).one_or_none()
        self.assertIsNotNone(cart)
        self.assert_equal_cart(cart, cart_request)
        self.assertEqual(cart.cart_products.count(), 0)

    def test_create_cart_with_products(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(fixtures.create_look_request(user_id=str(user.id)))
        role = self.role_service.create_role(fixtures.role_request(event_id=str(event.id)))
        attendee = self.attendee_service.create_attendee(
            fixtures.attendee_request(email=user.email, event_id=str(event.id), role=str(role.id), look_id=str(look.id))
        )

        # when
        cart_request = fixtures.create_cart_request(
            user_id=str(user.id),
            event_id=str(event.id),
            attendee_id=str(attendee.id),
            products=[fixtures.create_cart_product_request(), fixtures.create_cart_product_request()],
        )

        response = self.client.open(
            "/carts",
            query_string=self.hmac_query_params,
            data=json.dumps(cart_request, cls=encoder.CustomJSONEncoder),
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        cart_id = response.json
        self.assertIsNotNone(cart_id)
        cart = Cart.query.filter_by(id=cart_id).one_or_none()
        self.assertIsNotNone(cart)
        self.assert_equal_cart(cart, cart_request)
        products = cart.cart_products.all()
        self.assertEqual(len(products), 2)
        product_1 = products[0]
        self.assertIsNotNone(product_1)
        self.assert_equal_cart_product(product_1, cart_request["products"][0])
        product_2 = products[1]
        self.assertIsNotNone(product_2)
        self.assert_equal_cart_product(product_2, cart_request["products"][1])

    def test_get_cart_by_id(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(fixtures.create_look_request(user_id=str(user.id)))
        role = self.role_service.create_role(fixtures.role_request(event_id=str(event.id)))
        attendee = self.attendee_service.create_attendee(
            fixtures.attendee_request(email=user.email, event_id=str(event.id), role=str(role.id), look_id=str(look.id))
        )
        cart = self.cart_service.create_cart(
            dict(
                user_id=str(user.id),
                event_id=str(event.id),
                attendee_id=str(attendee.id),
                products=[
                    fixtures.create_cart_product_request(),
                    fixtures.create_cart_product_request(),
                    fixtures.create_cart_product_request(),
                ],
            )
        )

        # when
        response = self.client.open(
            "/cart_by_id",
            query_string={**self.hmac_query_params.copy(), "cart_id": str(cart.id)},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assert_equal_cart(cart, response.json)
        products = response.json["products"]
        self.assertEqual(len(products), 3)
        cart_products = CartProduct.query.filter_by(cart_id=cart.id).all()
        self.assert_equal_cart_product(cart_products[0], products[0])
        self.assert_equal_cart_product(cart_products[1], products[1])
        self.assert_equal_cart_product(cart_products[2], products[2])

    def test_get_cart_by_id_not_found(self):
        # when
        response = self.client.open(
            "/cart_by_id",
            query_string={**self.hmac_query_params.copy(), "cart_id": str(uuid.uuid4())},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_get_cart_by_event_attendee(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(fixtures.create_look_request(user_id=str(user.id)))
        role = self.role_service.create_role(fixtures.role_request(event_id=str(event.id)))
        attendee = self.attendee_service.create_attendee(
            fixtures.attendee_request(email=user.email, event_id=str(event.id), role=str(role.id), look_id=str(look.id))
        )
        cart = self.cart_service.create_cart(
            dict(
                user_id=str(user.id),
                event_id=str(event.id),
                attendee_id=str(attendee.id),
                products=[
                    fixtures.create_cart_product_request(),
                ],
            )
        )

        # when
        response = self.client.open(
            "/cart_by_event_attendee",
            query_string={**self.hmac_query_params, "event_id": str(event.id), "attendee_id": str(attendee.id)},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assert_equal_cart(cart, response.json)
        products = response.json["products"]
        self.assertEqual(len(products), 1)

    def test_update_cart_not_found(self):
        # when
        update_cart_request = fixtures.update_cart_request()

        response = self.client.open(
            "/carts",
            query_string=self.hmac_query_params,
            data=json.dumps(update_cart_request, cls=encoder.CustomJSONEncoder),
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_update_cart(self):
        # when
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(fixtures.create_look_request(user_id=str(user.id)))
        role = self.role_service.create_role(fixtures.role_request(event_id=str(event.id)))
        attendee = self.attendee_service.create_attendee(
            fixtures.attendee_request(email=user.email, event_id=str(event.id), role=str(role.id), look_id=str(look.id))
        )
        cart = self.cart_service.create_cart(
            dict(
                user_id=str(user.id),
                event_id=str(event.id),
                attendee_id=str(attendee.id),
                products=[
                    fixtures.create_cart_product_request(),
                    fixtures.create_cart_product_request(),
                    fixtures.create_cart_product_request(),
                ],
            )
        )

        update_cart_request = fixtures.update_cart_request(
            id=str(cart.id),
            user_id=str(user.id),
            event_id=str(event.id),
            attendee_id=str(attendee.id),
            products=[
                fixtures.create_cart_product_request(),
                fixtures.create_cart_product_request(),
            ],
        )

        response = self.client.open(
            "/carts",
            query_string=self.hmac_query_params,
            data=json.dumps(update_cart_request, cls=encoder.CustomJSONEncoder),
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
