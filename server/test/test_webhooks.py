import json
import random
import uuid

from server import encoder
from server.database.models import DiscountType
from server.services.discount import GROOM_DISCOUNT_VIRTUAL_PRODUCT_PREFIX, GROOM_GIFT_DISCOUNT_CODE_PREFIX
from server.test import BaseTestCase
from . import fixtures

PAID_ORDER_REQUEST_HEADERS = {
    "Accept": "application/json",
    "X-Shopify-Topic": "orders/paid",
}

WEBHOOK_SHOPIFY_ENDPOINT = "/webhooks/shopify"


class TestWebhooks(BaseTestCase):
    def __post(self, payload, headers=None):
        return self.client.open(
            WEBHOOK_SHOPIFY_ENDPOINT,
            method="POST",
            data=json.dumps(payload, cls=encoder.CustomJSONEncoder),
            headers=PAID_ORDER_REQUEST_HEADERS if not headers else headers,
            content_type=self.content_type,
        )

    def test_webhook_without_topic_header(self):
        # when
        response = self.__post({}, self.request_headers)

        # then
        self.assert400(response)

    def test_unsupported_webhook_type(self):
        # when
        response = self.__post(
            {},
            {
                "Accept": "application/json",
                "X-Shopify-Topic": f"orders/{uuid.uuid4()}",
            },
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 0)

    def test_paid_order_without_items(self):
        # when
        response = self.__post({})

        # then
        self.assert200(response)
        self.assertTrue("No items in order" in response.json["errors"])

    def test_paid_order_for_non_groom_gift_virtual_product(self):
        # when
        response = self.__post(fixtures.shopify_paid_order_gift_virtual_product_pay_for_discounts())

        # then
        self.assert200(response)
        self.assertEqual(response.text, "")

    def test_paid_order_with_groom_gift_virtual_product_sku(self):
        # when
        response = self.__post(
            fixtures.shopify_paid_order_gift_virtual_product_pay_for_discounts(
                f"{GROOM_DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{random.randint(1000, 1000000)}"
            )
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
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 500),
            DiscountType.GROOM_GIFT,
            shopify_virtual_product_id=product_id,
        )

        # when
        response = self.__post(
            fixtures.shopify_paid_order_gift_virtual_product_pay_for_discounts(
                f"{GROOM_DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{random.randint(1000, 1000000)}", product_id=product_id
            )
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
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 500),
            DiscountType.GROOM_GIFT,
            shopify_virtual_product_id=product_id,
        )

        # when
        response = self.__post(
            fixtures.shopify_paid_order_gift_virtual_product_pay_for_discounts(
                f"{GROOM_DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{random.randint(1000, 1000000)}", product_id=product_id
            )
        )

        # then
        self.assert200(response)
        self.assertTrue("No shopify variants founds for look" in response.json["errors"])

    def test_paid_order(self):
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
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 500),
            DiscountType.GROOM_GIFT,
            shopify_virtual_product_id=product_id,
        )

        # when
        response = self.__post(
            fixtures.shopify_paid_order_gift_virtual_product_pay_for_discounts(
                f"{GROOM_DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{random.randint(1000, 1000000)}", product_id=product_id
            )
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json.get("discount_codes")), 1)

        discount_codes = response.json.get("discount_codes")

        self.assertTrue(discount_codes[0].startswith(GROOM_GIFT_DISCOUNT_CODE_PREFIX))

    def test_paid_order_with_groom_1_paid_and_1_unpaid_discounts(self):
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
            DiscountType.GROOM_GIFT,
            False,
            f"{GROOM_GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )
        product_id = random.randint(1000, 1000000)
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 500),
            DiscountType.GROOM_GIFT,
            shopify_virtual_product_id=product_id,
        )

        # when
        response = self.__post(
            fixtures.shopify_paid_order_gift_virtual_product_pay_for_discounts(
                f"{GROOM_DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{random.randint(1000, 1000000)}", product_id=product_id
            )
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json.get("discount_codes")), 1)

        discount_codes = response.json.get("discount_codes")

        self.assertTrue(discount_codes[0].startswith(GROOM_GIFT_DISCOUNT_CODE_PREFIX))

    def test_paid_order_with_groom_multiple_discount_intents(self):
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
        discount_intent1 = self.app.discount_service.create_discount(
            event.id,
            attendee1.id,
            random.randint(50, 500),
            DiscountType.GROOM_GIFT,
            shopify_virtual_product_id=product_id,
        )
        discount_intent2 = self.app.discount_service.create_discount(
            event.id,
            attendee2.id,
            random.randint(50, 500),
            DiscountType.GROOM_GIFT,
            shopify_virtual_product_id=product_id,
        )
        discount_intent3 = self.app.discount_service.create_discount(
            event.id,
            attendee3.id,
            random.randint(50, 500),
            DiscountType.GROOM_GIFT,
            shopify_virtual_product_id=product_id,
        )

        # when
        response = self.__post(
            fixtures.shopify_paid_order_gift_virtual_product_pay_for_discounts(
                f"{GROOM_DISCOUNT_VIRTUAL_PRODUCT_PREFIX}-{random.randint(1000, 1000000)}", product_id=product_id
            )
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json.get("discount_codes")), 3)

        discount_codes = response.json.get("discount_codes")

        self.assertTrue(
            discount_codes[0].startswith(f"{GROOM_GIFT_DISCOUNT_CODE_PREFIX}-{discount_intent1.amount}-OFF")
        )
        self.assertTrue(
            discount_codes[1].startswith(f"{GROOM_GIFT_DISCOUNT_CODE_PREFIX}-{discount_intent2.amount}-OFF")
        )
        self.assertTrue(
            discount_codes[2].startswith(f"{GROOM_GIFT_DISCOUNT_CODE_PREFIX}-{discount_intent3.amount}-OFF")
        )

    def test_paid_order_with_empty_list_of_discount_codes(self):
        # when
        response = self.__post(fixtures.shopify_paid_order_user_pays_for_order_with_discounts([]))

        # then
        self.assert200(response)
        self.assertEqual(response.text, "")

    def test_paid_order_with_non_existing_discount_codes(self):
        # when
        response = self.__post(fixtures.shopify_paid_order_user_pays_for_order_with_discounts(["ASDF1234"]))

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 0)

    def test_paid_order_with_discount_code(self):
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
        discount = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(10, 900),
            DiscountType.GROOM_GIFT,
            False,
            f"{GROOM_GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        response = self.__post(
            fixtures.shopify_paid_order_user_pays_for_order_with_discounts([discount.shopify_discount_code])
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0], discount.shopify_discount_code)

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
            DiscountType.GROOM_GIFT,
            False,
            f"{GROOM_GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        discount2 = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(10, 900),
            DiscountType.GROOM_GIFT,
            False,
            f"{GROOM_GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        response = self.__post(
            fixtures.shopify_paid_order_user_pays_for_order_with_discounts(
                [discount1.shopify_discount_code, discount2.shopify_discount_code]
            )
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 2)
        self.assertEqual(
            {response.json[0], response.json[1]}, {discount1.shopify_discount_code, discount2.shopify_discount_code}
        )
