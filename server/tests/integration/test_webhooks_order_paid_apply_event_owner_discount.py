import random

from server.database.models import DiscountType
from server.services.discount import GIFT_DISCOUNT_CODE_PREFIX
from server.tests.integration import BaseTestCase, fixtures, WEBHOOK_SHOPIFY_ENDPOINT

PAID_ORDER_REQUEST_HEADERS = {
    "X-Shopify-Topic": "orders/paid",
}


class TestWebhooksOrderPaidEventOwnerDiscount(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_order_with_empty_list_of_discount_codes(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(
                discounts=[], customer_email=user.email, line_items=[fixtures.webhook_shopify_line_item()]
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json["discount_codes"], [])

    def test_order_with_non_existing_discount_codes(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(
                discounts=["ASDF1234"], customer_email=user.email, line_items=[fixtures.webhook_shopify_line_item()]
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json["discount_codes"]), 0)

    def test_order_with_discount_code(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )
        discount = self.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(10, 900),
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(
                customer_email=user.email,
                discounts=[discount.shopify_discount_code],
                line_items=[fixtures.webhook_shopify_line_item()],
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json["discount_codes"][0], discount.shopify_discount_code)

        discount_in_db = self.discount_service.get_discount_by_shopify_code(discount.shopify_discount_code)
        self.assertTrue(discount_in_db.used)

    def test_order_with_multiple_discount_codes(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )
        discount1 = self.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(10, 900),
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        discount2 = self.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(10, 900),
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(
                customer_email=user.email,
                discounts=[discount1.shopify_discount_code, discount2.shopify_discount_code],
                line_items=[fixtures.webhook_shopify_line_item()],
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)

        discount_codes = response.json["discount_codes"]
        self.assertEqual(len(discount_codes), 2)
        self.assertEqual(
            {discount_codes[0], discount_codes[1]}, {discount1.shopify_discount_code, discount2.shopify_discount_code}
        )
