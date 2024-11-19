import json
from uuid import UUID

from server import encoder
from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures


class TestMeasurements(BaseTestCase):
    def test_create_measurements(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        response = self.client.open(
            "/measurements",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.store_measurement_request(user_id=user.id).model_dump(), cls=encoder.CustomJSONEncoder
            ),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])

    def test_create_measurements_by_email(self):
        # given
        email = utils.generate_email()

        # when
        response = self.client.open(
            "/measurements",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.store_measurement_request(email=email).model_dump(), cls=encoder.CustomJSONEncoder
            ),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])
        measurement = self.measurement_service.get_measurement_by_id(UUID(response.json["id"]))
        self.assertIsNotNone(measurement)
        self.assertEqual(measurement.email, email)
        self.assertIsNone(measurement.user_id)

    def test_get_latest_measurements1(self):
        test_email = utils.generate_email()
        user = self.user_service.create_user(fixtures.create_user_request(email=test_email))
        measurement1 = self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=user.id))
        measurement2 = self.measurement_service.create_measurement(fixtures.store_measurement_request(email=test_email))

        # when
        latest_measurement = self.measurement_service.get_latest_measurement_for_user_by_id_or_email(
            user_id=user.id, email=test_email
        )

        # then
        self.assertEqual(latest_measurement.id, measurement2.id)

    def test_get_latest_measurements2(self):
        test_email = utils.generate_email()
        user = self.user_service.create_user(fixtures.create_user_request(email=test_email))
        measurement1 = self.measurement_service.create_measurement(fixtures.store_measurement_request(email=test_email))
        measurement2 = self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=user.id))

        # when
        latest_measurement = self.measurement_service.get_latest_measurement_for_user_by_id_or_email(
            user_id=user.id, email=test_email
        )

        # then
        self.assertEqual(latest_measurement.id, measurement2.id)

    def test_get_latest_measurements3(self):
        test_email = utils.generate_email()
        user = self.user_service.create_user(fixtures.create_user_request(email=test_email))
        measurement1 = self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=user.id))
        measurement2 = self.measurement_service.create_measurement(
            fixtures.store_measurement_request(user_id=user.id, email=test_email)
        )
        measurement3 = self.measurement_service.create_measurement(fixtures.store_measurement_request(email=test_email))

        # when
        latest_measurement = self.measurement_service.get_latest_measurement_for_user_by_id_or_email(
            user_id=user.id, email=test_email
        )

        # then
        self.assertEqual(latest_measurement.id, measurement3.id)

    def test_get_latest_measurements4(self):
        test_email = utils.generate_email()
        user = self.user_service.create_user(fixtures.create_user_request(email=test_email))
        measurement1 = self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=user.id))
        measurement2 = self.measurement_service.create_measurement(fixtures.store_measurement_request(email=test_email))

        # when
        latest_measurement = self.measurement_service.get_latest_measurement_for_user_by_id_or_email(user_id=user.id)

        # then
        self.assertEqual(latest_measurement.id, measurement2.id)
