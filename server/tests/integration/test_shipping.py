import json
from datetime import timedelta, datetime

from parameterized import parameterized

from server.database.database_manager import db
from server.database.models import Event
from server.models.event_model import EventModel
from server.models.shipping_model import (
    GROUND_SHIPPING_NAME,
    FREE_SHIPPING_PRICE_IN_CENTS,
    STANDARD_SHIPPING_PRICE_IN_CENTS,
    EXPEDITED_SHIPPING_NAME,
    EXPEDITED_SHIPPING_PRICE_IN_CENTS,
)
from server.tests.integration import BaseTestCase, fixtures


class TestShipping(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    @staticmethod
    def __change_event_at_via_db(event_id, weeks=10):
        db_event = Event.query.filter(Event.id == event_id).first()
        db_event.event_at = datetime.now() + timedelta(weeks=weeks)
        db.session.commit()
        db.session.refresh(db_event)

        return EventModel.model_validate(db_event)

    def test_shipping_no_items(self):
        # when
        response = self.client.open(
            "/shipping/price",
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(fixtures.shipping_rate_request([])),
        )

        # then
        self.assertStatus(response, 200)
        rate = response.json.get("rates", {})[0]
        self.assertEqual(rate.get("service_name"), GROUND_SHIPPING_NAME)
        self.assertEqual(rate.get("total_price"), FREE_SHIPPING_PRICE_IN_CENTS)

    def test_shipping_few_items_with_total_price_zero(self):
        # when
        response = self.client.open(
            "/shipping/price",
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                fixtures.shipping_rate_request(
                    [fixtures.shipping_item(price=0), fixtures.shipping_item(price=0), fixtures.shipping_item(price=0)]
                )
            ),
        )

        # then
        self.assertStatus(response, 200)
        rate = response.json.get("rates", {})[0]
        self.assertEqual(rate.get("service_name"), GROUND_SHIPPING_NAME)
        self.assertEqual(rate.get("total_price"), FREE_SHIPPING_PRICE_IN_CENTS)

    def test_shipping_an_item_with_price_below_210(self):
        # when
        response = self.client.open(
            "/shipping/price",
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(fixtures.shipping_rate_request([fixtures.shipping_item(price=12000)])),
        )

        # then
        self.assertStatus(response, 200)
        rate = response.json.get("rates", {})[0]
        self.assertEqual(rate.get("service_name"), GROUND_SHIPPING_NAME)
        self.assertEqual(rate.get("total_price"), STANDARD_SHIPPING_PRICE_IN_CENTS)

    def test_shipping_an_item_with_price_above_210(self):
        # when
        response = self.client.open(
            "/shipping/price",
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(fixtures.shipping_rate_request([fixtures.shipping_item(price=30100)])),
        )

        # then
        self.assertStatus(response, 200)
        rate = response.json.get("rates", {})[0]
        self.assertEqual(rate.get("service_name"), GROUND_SHIPPING_NAME)
        self.assertEqual(rate.get("total_price"), FREE_SHIPPING_PRICE_IN_CENTS)

    def test_shipping_few_items_total_below_210(self):
        # when
        response = self.client.open(
            "/shipping/price",
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                fixtures.shipping_rate_request(
                    [
                        fixtures.shipping_item(price=5000),
                        fixtures.shipping_item(price=6000),
                        fixtures.shipping_item(price=7000),
                        fixtures.shipping_item(price=0),
                    ]
                )
            ),
        )

        # then
        self.assertStatus(response, 200)
        rate = response.json.get("rates", {})[0]
        self.assertEqual(rate.get("service_name"), GROUND_SHIPPING_NAME)
        self.assertEqual(rate.get("total_price"), STANDARD_SHIPPING_PRICE_IN_CENTS)

    def test_shipping_few_items_total_above_210(self):
        # when
        response = self.client.open(
            "/shipping/price",
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                fixtures.shipping_rate_request(
                    [
                        fixtures.shipping_item(price=5000),
                        fixtures.shipping_item(price=6000),
                        fixtures.shipping_item(price=17000),
                        fixtures.shipping_item(price=0),
                    ]
                )
            ),
        )

        # then
        self.assertStatus(response, 200)
        rate = response.json.get("rates", {})[0]
        self.assertEqual(rate.get("service_name"), GROUND_SHIPPING_NAME)
        self.assertEqual(rate.get("total_price"), FREE_SHIPPING_PRICE_IN_CENTS)

    def test_shipping_suit_bundle_not_associated_with_any_attendee(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )

        # when
        shipping_items = []
        for item in look.product_specs.get("items", []):
            shipping_items.append(
                fixtures.shipping_item(
                    product_id=item.get("product_id"),
                    variant_id=item.get("variant_id"),
                    sku=item.get("variant_sku"),
                    price=int(item.get("variant_price") * 100),  # convert to cents
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
        self.assertEqual(rate.get("total_price"), FREE_SHIPPING_PRICE_IN_CENTS)

    @parameterized.expand(
        [
            [[10], GROUND_SHIPPING_NAME, FREE_SHIPPING_PRICE_IN_CENTS],  # event in the future
            [[-10], GROUND_SHIPPING_NAME, FREE_SHIPPING_PRICE_IN_CENTS],  # event in the past
            [[5], EXPEDITED_SHIPPING_NAME, EXPEDITED_SHIPPING_PRICE_IN_CENTS],  # event in expedited shipping window
            [[-10, 10], GROUND_SHIPPING_NAME, FREE_SHIPPING_PRICE_IN_CENTS],  # not in expedited shipping window
            [[-10, 5], EXPEDITED_SHIPPING_NAME, EXPEDITED_SHIPPING_PRICE_IN_CENTS],  # one in expedited shipping window
            [[-10, -20], GROUND_SHIPPING_NAME, FREE_SHIPPING_PRICE_IN_CENTS],  # few past events
            [[10, 20], GROUND_SHIPPING_NAME, FREE_SHIPPING_PRICE_IN_CENTS],  # few future events
            [[10, 5], GROUND_SHIPPING_NAME, FREE_SHIPPING_PRICE_IN_CENTS],  # one future and one expedited events
            [[3, 5], EXPEDITED_SHIPPING_NAME, EXPEDITED_SHIPPING_PRICE_IN_CENTS],  # few expedited events
            [[3, 5, 10], GROUND_SHIPPING_NAME, FREE_SHIPPING_PRICE_IN_CENTS],  # 2 expedited and 1 future event
        ]
    )
    def test_shipping_looks_belong_to_event_in_past_and_future(self, weeks, shipping_name, shipping_price):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())

        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        for week in weeks:
            event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
            self.__change_event_at_via_db(event.id, week)
            attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
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
                    price=int(item.get("variant_price") * 100),  # convert to cents
                    name=item.get("variant_title"),
                )
            )

        response = self.client.open(
            "/shipping/price",
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(fixtures.shipping_rate_request(shipping_items)),
        )

        # then
        self.assertStatus(response, 200)
        rate = response.json.get("rates", {})[0]
        self.assertEqual(rate.get("service_name"), shipping_name)
        self.assertEqual(rate.get("total_price"), shipping_price)
