import json
from datetime import timedelta, datetime

from server.models.shipping_model import (
    GROUND_SHIPPING_NAME,
    GROUND_SHIPPING_PRICE_IN_CENTS,
    EXPEDITED_SHIPPING_NAME,
    EXPEDITED_SHIPPING_PRICE_IN_CENTS,
)
from server.tests.integration import BaseTestCase, fixtures


class TestShipping(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_shipping_no_items(self):
        # when
        response = self.client.open(
            "/shipping/price",
            # query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(fixtures.shipping_rate_request([])),
        )

        # then
        self.assertStatus(response, 200)
        rate = response.json.get("rates", {})[0]
        self.assertEqual(rate.get("service_name"), GROUND_SHIPPING_NAME)
        self.assertEqual(rate.get("total_price"), GROUND_SHIPPING_PRICE_IN_CENTS)

    def test_shipping_just_an_items(self):
        # when
        response = self.client.open(
            "/shipping/price",
            # query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(fixtures.shipping_rate_request([fixtures.shipping_item()])),
        )

        # then
        self.assertStatus(response, 200)
        rate = response.json.get("rates", {})[0]
        self.assertEqual(rate.get("service_name"), GROUND_SHIPPING_NAME)
        self.assertEqual(rate.get("total_price"), GROUND_SHIPPING_PRICE_IN_CENTS)

    def test_shipping_event_6_weeks_plus(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )

        # when
        shipping_items = []
        for item in look.product_specs.get("items", []):
            shipping_items.append(
                fixtures.shipping_item(
                    product_id=item.get("product_id"),
                    variant_id=item.get("variant_id"),
                    sku=item.get("variant_sku"),
                    price=item.get("variant_price"),
                    name=item.get("variant_title"),
                )
            )

        response = self.client.open(
            "/shipping/price",
            # query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(fixtures.shipping_rate_request(shipping_items)),
        )

        # then
        self.assertStatus(response, 200)
        rate = response.json.get("rates", {})[0]
        self.assertEqual(rate.get("service_name"), GROUND_SHIPPING_NAME)
        self.assertEqual(rate.get("total_price"), GROUND_SHIPPING_PRICE_IN_CENTS)

    def test_shipping_event_less_then_6_weeks(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(
            fixtures.create_event_request(user_id=user.id, event_at=(datetime.now() + timedelta(weeks=3)).isoformat()),
            ignore_event_date_creation_condition=True,
        )
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )

        # when
        shipping_items = []
        for item in look.product_specs.get("items", []):
            shipping_items.append(
                fixtures.shipping_item(
                    product_id=item.get("product_id"),
                    variant_id=item.get("variant_id"),
                    sku=item.get("variant_sku"),
                    price=item.get("variant_price"),
                    name=item.get("variant_title"),
                )
            )

        response = self.client.open(
            "/shipping/price",
            # query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(fixtures.shipping_rate_request(shipping_items)),
        )

        # then
        self.assertStatus(response, 200)
        rate = response.json.get("rates", {})[0]
        self.assertEqual(rate.get("service_name"), EXPEDITED_SHIPPING_NAME)
        self.assertEqual(rate.get("total_price"), EXPEDITED_SHIPPING_PRICE_IN_CENTS)
