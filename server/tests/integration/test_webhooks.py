import json
import random
import uuid

from server import encoder
from server.database.models import DiscountType
from server.services.discount import DISCOUNT_VIRTUAL_PRODUCT_PREFIX, GIFT_DISCOUNT_CODE_PREFIX
from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures

PAID_ORDER_REQUEST_HEADERS = {
    "X-Shopify-Topic": "orders/paid",
}

CUSTOMERS_CREATE_REQUEST_HEADERS = {
    "X-Shopify-Topic": "customers/create",
}

CUSTOMERS_UPDATE_REQUEST_HEADERS = {
    "X-Shopify-Topic": "customers/update",
}

CUSTOMERS_ENABLE_REQUEST_HEADERS = {
    "X-Shopify-Topic": "customers/enable",
}

CUSTOMERS_DISABLE_REQUEST_HEADERS = {
    "X-Shopify-Topic": "customers/disable",
}

WEBHOOK_SHOPIFY_ENDPOINT = "/webhooks/shopify"


class TestWebhooks(BaseTestCase):
    def __post(self, payload, headers):
        return self.client.open(
            WEBHOOK_SHOPIFY_ENDPOINT,
            method="POST",
            data=json.dumps(payload, cls=encoder.CustomJSONEncoder),
            headers={**self.request_headers, **headers},
            content_type=self.content_type,
        )

    def test_webhook_without_topic_header(self):
        # when
        response = self.__post({}, {})

        # then
        self.assert400(response)

    def test_unsupported_webhook_type(self):
        # when
        response = self.__post(
            {},
            {
                "X-Shopify-Topic": f"orders/{uuid.uuid4()}",
            },
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 0)

    def test_customers_create_event(self):
        # when
        webhook_customer = fixtures.webhook_customer_update(phone=random.randint(1000000000, 9999999999))
        response = self.__post(webhook_customer, CUSTOMERS_CREATE_REQUEST_HEADERS)

        # then
        self.assert200(response)
        user = self.user_service.get_user_by_email(webhook_customer["email"])
        self.assertIsNotNone(user)
        self.assertEqual(user.email, webhook_customer["email"])
        self.assertEqual(user.phone_number, str(webhook_customer["phone"]))
        self.assertEqual(user.first_name, webhook_customer["first_name"])
        self.assertEqual(user.last_name, webhook_customer["last_name"])
        self.assertEqual(user.shopify_id, str(webhook_customer["id"]))
        self.assertEqual(user.account_status, webhook_customer["state"] == "enabled")

    def test_customers_update_event(self):
        # given
        user = self.app.user_service.create_user(
            fixtures.create_user_request(
                shopify_id=str(random.randint(1000, 1000000)), phone_number=utils.generate_phone_number()
            )
        )

        # when
        webhook_customer = fixtures.webhook_customer_update(
            shopify_id=int(user.shopify_id),
            email=user.email,
            phone=random.randint(1000000000, 9999999999),
            account_status=not user.account_status,
        )
        response = self.__post(webhook_customer, CUSTOMERS_UPDATE_REQUEST_HEADERS)

        # then
        self.assert200(response)
        user = self.user_service.get_user_by_email(webhook_customer["email"])

        self.assertIsNotNone(user)
        self.assertEqual(user.email, webhook_customer["email"])
        self.assertEqual(user.phone_number, str(webhook_customer["phone"]))
        self.assertEqual(user.first_name, webhook_customer["first_name"])
        self.assertEqual(user.last_name, webhook_customer["last_name"])
        self.assertEqual(user.shopify_id, str(webhook_customer["id"]))
        self.assertEqual(user.account_status, webhook_customer["state"] == "enabled")

    def test_customers_disable_event(self):
        # given
        user = self.app.user_service.create_user(
            fixtures.create_user_request(shopify_id=str(random.randint(1000, 1000000)), account_status=True)
        )

        # when
        webhook_customer = fixtures.webhook_customer_update(
            shopify_id=int(user.shopify_id),
            email=user.email,
            account_status=False,
        )
        response = self.__post(webhook_customer, CUSTOMERS_DISABLE_REQUEST_HEADERS)

        # then
        self.assert200(response)
        user = self.user_service.get_user_by_email(webhook_customer["email"])

        self.assertIsNotNone(user)
        self.assertEqual(user.account_status, False)

    def test_customers_enable_event(self):
        # given
        user = self.app.user_service.create_user(
            fixtures.create_user_request(shopify_id=str(random.randint(1000, 1000000)), account_status=False)
        )

        # when
        webhook_customer = fixtures.webhook_customer_update(
            shopify_id=int(user.shopify_id),
            email=user.email,
            account_status=True,
        )
        response = self.__post(webhook_customer, CUSTOMERS_ENABLE_REQUEST_HEADERS)

        # then
        self.assert200(response)
        user = self.user_service.get_user_by_email(webhook_customer["email"])

        self.assertIsNotNone(user)
        self.assertEqual(user.account_status, True)

    def test_paid_order_without_items(self):
        # when
        response = self.__post({}, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        self.assertTrue("No items in order" in response.json["errors"])

    def test_paid_order_for_non_gift_virtual_product(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())

        # when
        response = self.__post(
            fixtures.webhook_shopify_paid_order(
                customer_email=user.email,
                line_items=[fixtures.webhook_shopify_line_item(sku=f"product-{utils.generate_unique_string()}")],
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json["discount_codes"], [])

    def test_paid_order_with_gift_virtual_product_sku(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())

        # when
        response = self.__post(
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

    def test_paid_order_no_look(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
        )
        product_id = random.randint(1000, 1000000)
        variant_id = random.randint(1000, 1000000)
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )

        # when
        response = self.__post(
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

    def test_paid_order_invalid_look(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(fixtures.create_look_request(user_id=attendee_user.id))
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )
        product_id = random.randint(1000, 1000000)
        variant_id = random.randint(1000, 1000000)
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )

        # when
        response = self.__post(
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
        self.assertTrue("No shopify variants founds for look" in response.json["errors"])

    def test_paid_order_with_one_discount_code(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id, product_specs={"variants": [random.randint(1000, 1000000)]}
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )
        product_id = random.randint(1000, 1000000)
        variant_id = random.randint(1000, 1000000)
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )

        # when
        response = self.__post(
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

    def test_paid_order_with_1_paid_and_1_unpaid_discounts(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id, product_specs={"variants": [random.randint(1000, 1000000)]}
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )
        self.app.discount_service.create_discount(
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
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )

        # when
        response = self.__post(
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

    def test_paid_order_with_multiple_discount_intents(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        look1 = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user1.id, product_specs={"variants": [random.randint(1000, 1000000)]}
            )
        )
        look2 = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user2.id, product_specs={"variants": [random.randint(1000, 1000000)]}
            )
        )
        look3 = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user3.id, product_specs={"variants": [random.randint(1000, 1000000)]}
            )
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user1.id, event_id=event.id, look_id=look1.id)
        )
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user2.id, event_id=event.id, look_id=look2.id)
        )
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user3.id, event_id=event.id, look_id=look3.id)
        )
        product_id = random.randint(1000, 1000000)
        variant_id = random.randint(1000, 1000000)
        discount_intent1 = self.app.discount_service.create_discount(
            event.id,
            attendee1.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )
        discount_intent2 = self.app.discount_service.create_discount(
            event.id,
            attendee2.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )
        discount_intent3 = self.app.discount_service.create_discount(
            event.id,
            attendee3.id,
            random.randint(50, 500),
            DiscountType.GIFT,
            shopify_virtual_product_id=product_id,
            shopify_virtual_product_variant_id=variant_id,
        )

        # when
        response = self.__post(
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

    def test_paid_order_with_empty_list_of_discount_codes(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())

        # when
        response = self.__post(
            fixtures.webhook_shopify_paid_order(
                discounts=[], customer_email=user.email, line_items=[fixtures.webhook_shopify_line_item()]
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json["discount_codes"], [])

    def test_paid_order_with_non_existing_discount_codes(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())

        # when
        response = self.__post(
            fixtures.webhook_shopify_paid_order(
                discounts=["ASDF1234"], customer_email=user.email, line_items=[fixtures.webhook_shopify_line_item()]
            ),
            PAID_ORDER_REQUEST_HEADERS,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json["discount_codes"]), 0)

    def test_paid_order_with_discount_code(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id,
                product_specs={
                    "bundle": {"variant_id": random.randint(1000, 1000000)},
                    "variants": [random.randint(1000, 1000000)],
                },
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )
        discount = self.app.discount_service.create_discount(
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
        response = self.__post(
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

    def test_paid_order_with_multiple_discount_codes(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id, product_specs={"variants": [random.randint(1000, 1000000)]}
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )
        discount1 = self.app.discount_service.create_discount(
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

        discount2 = self.app.discount_service.create_discount(
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
        response = self.__post(
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
        user = self.app.user_service.create_user(fixtures.create_user_request())

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=f"product-{utils.generate_unique_string()}")],
        )

        response = self.__post(webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order_id = response.json["id"]
        order = self.order_service.get_order_by_id(order_id)
        self.assertIsNotNone(order)
        self.assertEqual(len(order.products), 1)
        self.assertEqual(order.order_number, str(webhook_request["order_number"]))
        self.assertEqual(order.order_date.isoformat(), webhook_request["created_at"])
        self.assertIsNone(order.event_id)

        response_product = response.json["products"][0]
        request_line_item = webhook_request["line_items"][0]
        self.assertEqual(response_product["name"], request_line_item["name"])
        self.assertEqual(response_product["sku"], request_line_item["sku"])

    def test_order_paid_with_event(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event_id = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=f"product-{utils.generate_unique_string()}")],
            event_id=str(event_id),
        )

        response = self.__post(webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order_id = response.json["id"]
        order = self.order_service.get_order_by_id(order_id)
        self.assertIsNotNone(order)
        self.assertEqual(order.event_id, event_id)
