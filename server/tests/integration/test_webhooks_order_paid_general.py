import random

from server.database.models import DiscountType
from server.services.discount import DISCOUNT_VIRTUAL_PRODUCT_PREFIX, GIFT_DISCOUNT_CODE_PREFIX
from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures, WEBHOOK_SHOPIFY_ENDPOINT

PAID_ORDER_REQUEST_HEADERS = {
    "X-Shopify-Topic": "orders/paid",
}


class TestWebhooksOrderPaidGeneral(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_order_without_items(self):
        # when
        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, {}, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        self.assertTrue("No items in order" in response.json["errors"])

    def test_order_for_non_gift_virtual_product(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(
                customer_email=user.email,
                line_items=[fixtures.webhook_shopify_line_item(sku=f"product-{utils.generate_unique_string()}")],
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json["discount_codes"], [])

    def test_order_with_gift_virtual_product_sku(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(
                customer_email=user.email,
                line_items=[
                    fixtures.webhook_shopify_line_item(
                        sku=f"{DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{random.randint(1000, 1000000)}"
                    )
                ],
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertTrue("No discounts found for product" in response.json["errors"])

    def test_order_no_look(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
        )
        product_id = random.randint(1000, 1000000)
        variant_id = random.randint(1000, 1000000)
        self.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(
                customer_email=user.email,
                line_items=[
                    fixtures.webhook_shopify_line_item(
                        sku=f"{DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{random.randint(1000, 1000000)}",
                        product_id=product_id,
                        variant_id=variant_id,
                    )
                ],
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertTrue("No look associated for attendee" in response.json["errors"])

    def test_order_with_one_discount_code(self):
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
        product_id = random.randint(1000, 1000000)
        variant_id = random.randint(1000, 1000000)
        self.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(
                customer_email=user.email,
                line_items=[
                    fixtures.webhook_shopify_line_item(
                        sku=f"{DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{random.randint(1000, 1000000)}",
                        product_id=product_id,
                        variant_id=variant_id,
                    )
                ],
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json.get("discount_codes")), 1)

        discount_codes = response.json.get("discount_codes")

        self.assertTrue(discount_codes[0].startswith(GIFT_DISCOUNT_CODE_PREFIX))

    def test_order_with_1_paid_and_1_unpaid_discounts(self):
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
        self.discount_service.create_discount(
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
        product_id = random.randint(1000, 1000000)
        variant_id = random.randint(1000, 1000000)
        self.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(
                customer_email=user.email,
                line_items=[
                    fixtures.webhook_shopify_line_item(
                        sku=f"{DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{random.randint(1000, 1000000)}",
                        product_id=product_id,
                        variant_id=variant_id,
                    )
                ],
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json.get("discount_codes")), 1)

        discount_codes = response.json.get("discount_codes")

        self.assertTrue(discount_codes[0].startswith(GIFT_DISCOUNT_CODE_PREFIX))

    def test_order_with_multiple_discount_intents(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.user_service.create_user(fixtures.create_user_request())
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user1.id, product_specs=self.create_look_test_product_specs())
        )
        look2 = self.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user2.id, product_specs=self.create_look_test_product_specs())
        )
        look3 = self.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user3.id, product_specs=self.create_look_test_product_specs())
        )
        attendee1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user1.id, event_id=event.id, look_id=look1.id)
        )
        attendee2 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user2.id, event_id=event.id, look_id=look2.id)
        )
        attendee3 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user3.id, event_id=event.id, look_id=look3.id)
        )
        product_id = random.randint(1000, 1000000)
        variant_id = random.randint(1000, 1000000)
        discount_intent1 = self.discount_service.create_discount(
            event.id,
            attendee1.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )
        discount_intent2 = self.discount_service.create_discount(
            event.id,
            attendee2.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )
        discount_intent3 = self.discount_service.create_discount(
            event.id,
            attendee3.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )

        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            fixtures.webhook_shopify_paid_order(
                customer_email=user.email,
                line_items=[
                    fixtures.webhook_shopify_line_item(
                        sku=f"{DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{random.randint(1000, 1000000)}",
                        product_id=product_id,
                        variant_id=variant_id,
                    )
                ],
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json.get("discount_codes")), 3)

        discount_codes = response.json.get("discount_codes")

        self.assertTrue(discount_codes[0].startswith(f"{GIFT_DISCOUNT_CODE_PREFIX}-{int(discount_intent1.amount)}-OFF"))
        self.assertTrue(discount_codes[1].startswith(f"{GIFT_DISCOUNT_CODE_PREFIX}-{int(discount_intent2.amount)}-OFF"))
        self.assertTrue(discount_codes[2].startswith(f"{GIFT_DISCOUNT_CODE_PREFIX}-{int(discount_intent3.amount)}-OFF"))

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

    def test_order_paid_one_product(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=f"product-{utils.generate_unique_string()}")],
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order_id = response.json["id"]
        order = self.order_service.get_order_by_id(order_id)
        self.assertIsNotNone(order)
        self.assertEqual(len(order.products), 1)
        self.assertIsNotNone(order.shopify_order_id)
        self.assertEqual(order.shopify_order_id, str(webhook_request["id"]))
        self.assertIsNotNone(order.order_number)
        self.assertEqual(order.shopify_order_number, str(webhook_request["order_number"]))
        self.assertEqual(order.order_date.isoformat(), webhook_request["created_at"])
        self.assertIsNone(order.event_id)

        response_product = response.json["products"][0]
        request_line_item = webhook_request["line_items"][0]
        self.assertEqual(response_product["name"], request_line_item["name"])
        self.assertEqual(response_product["sku"], request_line_item["sku"])

    def test_order_paid_with_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event_id = self.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event_id, email=attendee_user.email)
        )

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=attendee_user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=f"product-{utils.generate_unique_string()}")],
            event_id=str(event_id),
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order_id = response.json["id"]
        order = self.order_service.get_order_by_id(order_id)
        self.assertIsNotNone(order)
        self.assertEqual(order.event_id, event_id)

        attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertTrue(attendee.pay)
