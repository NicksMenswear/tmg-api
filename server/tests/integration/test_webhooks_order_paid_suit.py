from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures, WEBHOOK_SHOPIFY_ENDPOINT

PAID_ORDER_REQUEST_HEADERS = {
    "X-Shopify-Topic": "orders/paid",
}


class TestWebhooksOrderPaidSuit(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_order_with_user_measurements_but_unknown_sku(self):
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
        self.assertEqual(order.products[0].sku, webhook_request["line_items"][0]["sku"])
        self.assertIsNone(order.products[0].shiphero_sku)
