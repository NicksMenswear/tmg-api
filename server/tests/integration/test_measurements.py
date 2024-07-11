import json

from server import encoder
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
