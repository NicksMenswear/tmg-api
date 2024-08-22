import json

from server import encoder
from server.services.order_service import ORDER_STATUS_PENDING_MEASUREMENTS, ORDER_STATUS_READY
from server.services.sku_builder_service import ProductType
from server.tests.integration import BaseTestCase, fixtures


class TestSizes(BaseTestCase):
    def test_create_size(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        measurement = self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=user.id))

        # when
        response = self.client.open(
            "/sizes",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.store_size_request(user_id=user.id, measurement_id=measurement.id).model_dump(),
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])

    def test_create_size_with_existing_attendees(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        user = self.user_service.create_user(fixtures.create_user_request())
        event1 = self.event_service.create_event(fixtures.create_event_request(user_id=str(owner.id)))
        event2 = self.event_service.create_event(fixtures.create_event_request(user_id=str(owner.id)))
        attendee1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=user.email, event_id=str(event1.id))
        )
        attendee2 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=user.email, event_id=str(event2.id))
        )
        measurement = self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=user.id))

        # when
        response = self.client.open(
            "/sizes",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.store_size_request(user_id=user.id, measurement_id=measurement.id).model_dump(),
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])

        # Size was set for existing attendees
        attendee1 = self.attendee_service.get_attendee_by_id(attendee1.id)
        self.assertTrue(attendee1.size)
        attendee2 = self.attendee_service.get_attendee_by_id(attendee2.id)
        self.assertTrue(attendee2.size)

    def test_create_size_and_new_attendee(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=str(owner.id)))
        measurement = self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=user.id))
        self.size_service.create_size(fixtures.store_size_request(user_id=str(user.id), measurement_id=measurement.id))

        # when
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=user.email, event_id=str(event.id))
        )

        # then
        # Size is set for every new attendee
        self.assertTrue(attendee.size)
        attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertTrue(attendee.size)

    def test_create_size_for_and_there_is_pending_order(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        measurement = self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=user.id))
        order = self.order_service.create_order(
            fixtures.create_order_request(user_id=user.id, status=ORDER_STATUS_PENDING_MEASUREMENTS)
        )
        self.order_service.create_order_item(
            fixtures.create_order_item_request(
                order_id=order.id, shopify_sku=self.get_random_shopify_sku_by_product_type(ProductType.PANTS)
            )
        )

        # when
        response = self.client.open(
            "/sizes",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.store_size_request(user_id=user.id, measurement_id=measurement.id).model_dump(),
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        order = self.order_service.get_order_by_id(order.id)
        self.assertEqual(order.status, ORDER_STATUS_READY)
        self.assertEqual(order.meta.get("measurements_id"), str(measurement.id))
        self.assertIsNotNone(order.meta.get("sizes_id"))
