import json

from server.tests.integration import BaseTestCase, fixtures


class TestMeasurements(BaseTestCase):
    def test_create_measurements(self):
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        response = self.client.open(
            "/measurements",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(fixtures.store_size_request(user_id=user.id)),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])
