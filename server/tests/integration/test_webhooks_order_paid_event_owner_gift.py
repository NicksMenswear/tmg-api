import random

from server.database.models import DiscountType, Discount
from server.services.discount_service import DISCOUNT_VIRTUAL_PRODUCT_PREFIX, GIFT_DISCOUNT_CODE_PREFIX
from server.tests.integration import BaseTestCase, fixtures, WEBHOOK_SHOPIFY_ENDPOINT

PAID_ORDER_REQUEST_HEADERS = {
    "X-Shopify-Topic": "orders/paid",
}


class TestWebhooksOrderPaidEventOwnerGift(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_order_no_discounts(self):
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
        self.assertTrue(len(response.json) == 0)

    def test_order_discount_product(self):
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
        self.assertTrue(len(response.json) == 0)

    def test_order_with_one_discount_code(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user.email, event_id=event.id, look_id=look.id)
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
        discounts = Discount.query.filter(Discount.attendee_id == attendee.id).all()
        self.assertEqual(len(discounts), 1)
        self.assertIsNotNone(discounts[0].shopify_discount_code)
        self.assertIsNotNone(discounts[0].shopify_discount_code_id)
        self.assertTrue(discounts[0].shopify_discount_code.startswith(GIFT_DISCOUNT_CODE_PREFIX))

    def test_order_with_1_paid_and_1_unpaid_discounts(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user.email, event_id=event.id, look_id=look.id)
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
        discounts = Discount.query.filter(Discount.attendee_id == attendee.id).all()
        self.assertEqual(len(discounts), 2)
        self.assertIsNotNone(discounts[0].shopify_discount_code)
        self.assertIsNotNone(discounts[0].shopify_discount_code_id)
        self.assertTrue(discounts[0].shopify_discount_code.startswith(GIFT_DISCOUNT_CODE_PREFIX))
        self.assertIsNotNone(discounts[1].shopify_discount_code)
        self.assertIsNotNone(discounts[1].shopify_discount_code_id)
        self.assertTrue(discounts[1].shopify_discount_code.startswith(GIFT_DISCOUNT_CODE_PREFIX))

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
            fixtures.create_attendee_request(email=attendee_user1.email, event_id=event.id, look_id=look1.id)
        )
        attendee2 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user2.email, event_id=event.id, look_id=look2.id)
        )
        attendee3 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user3.email, event_id=event.id, look_id=look3.id)
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
        discounts1 = Discount.query.filter(Discount.attendee_id == attendee1.id).all()
        self.assertEqual(len(discounts1), 1)
        self.assertIsNotNone(discounts1[0].shopify_discount_code)
        self.assertIsNotNone(discounts1[0].shopify_discount_code_id)
        self.assertTrue(
            discounts1[0].shopify_discount_code.startswith(
                f"{GIFT_DISCOUNT_CODE_PREFIX}-{int(discount_intent1.amount)}-OFF"
            )
        )
        discounts2 = Discount.query.filter(Discount.attendee_id == attendee2.id).all()
        self.assertIsNotNone(discounts2[0].shopify_discount_code)
        self.assertIsNotNone(discounts2[0].shopify_discount_code_id)
        self.assertTrue(
            discounts2[0].shopify_discount_code.startswith(
                f"{GIFT_DISCOUNT_CODE_PREFIX}-{int(discount_intent2.amount)}-OFF"
            )
        )
        discounts3 = Discount.query.filter(Discount.attendee_id == attendee3.id).all()
        self.assertIsNotNone(discounts3[0].shopify_discount_code)
        self.assertIsNotNone(discounts3[0].shopify_discount_code_id)
        self.assertTrue(
            discounts3[0].shopify_discount_code.startswith(
                f"{GIFT_DISCOUNT_CODE_PREFIX}-{int(discount_intent3.amount)}-OFF"
            )
        )
