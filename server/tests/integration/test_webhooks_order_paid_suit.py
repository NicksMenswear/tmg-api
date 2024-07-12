from parameterized import parameterized

from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures, WEBHOOK_SHOPIFY_ENDPOINT

PAID_ORDER_REQUEST_HEADERS = {
    "X-Shopify-Topic": "orders/paid",
}


class TestWebhooksOrderPaidSuit(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_order_with_unknown_sku(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event_id = self.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        self.size_service.create_size(fixtures.store_size_request(user_id=attendee_user.id))
        self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=attendee_user.id))
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event_id, email=attendee_user.email)
        )

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=attendee_user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=f"invalid-{utils.generate_unique_string()}")],
            event_id=str(event_id),
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order = self.order_service.get_order_by_id(response.json["id"])
        self.assertIsNotNone(order)
        self.assertEqual(order.products[0].shopify_sku, webhook_request["line_items"][0]["sku"])
        self.assertIsNone(order.products[0].sku)

    @parameterized.expand(
        [
            [["101A1BLK"], ["101A1BLK42RAF"]],  # jacket
            [["201A1BLK"], ["201A1BLK40R"]],  # pants
            [["301A2BLK"], ["301A2BLK00LRAF"]],  # vest
            [["403A2BLK"], ["403A2BLK1605"]],  # shirt
            [["503A400A"], ["503A400AOSR"]],  # bow tie
            [["603A400A"], ["603A400AOSR"]],  # tie
            [["703A4BLK"], ["703A4BLK460R"]],  # belt
            [["803A4BLK"], ["803A4BLK070D"]],  # shoes
            [["903A4BLK"], ["903A4BLKOSR"]],  # socks
            [
                ["101A1BLK", "201A1BLK", "301A2BLK", "903A4BLK"],
                ["101A1BLK42RAF", "201A1BLK40R", "301A2BLK00LRAF", "903A4BLKOSR"],
            ],
        ]
    )
    def test_order_shiphero_skus(self, shopify_skus, shiphero_skus):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event_id = self.event_service.create_event(fixtures.create_event_request(user_id=user.id)).id
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        self.size_service.create_size(fixtures.store_size_request(user_id=attendee_user.id))
        self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=attendee_user.id))
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event_id, email=attendee_user.email)
        )

        # when
        webhook_request = fixtures.webhook_shopify_paid_order(
            customer_email=attendee_user.email,
            line_items=[fixtures.webhook_shopify_line_item(sku=shopify_sku) for shopify_sku in shopify_skus],
            event_id=str(event_id),
        )

        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_request, PAID_ORDER_REQUEST_HEADERS)

        # then
        self.assert200(response)
        order = self.order_service.get_order_by_id(response.json["id"])
        self.assertIsNotNone(order)

        response_shopify_skus = set([product.shopify_sku for product in order.products])
        response_shiphero_skus = set([product.sku for product in order.products])

        self.assertEqual(response_shopify_skus, set(shopify_skus))
        self.assertEqual(response_shiphero_skus, set(shiphero_skus))
