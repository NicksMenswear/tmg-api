import json

from server.tests.integration import BaseTestCase, fixtures


class TestMeasurements(BaseTestCase):
    def test_create_measurements(self):
        # when
        response = self.client.open(
            "/measurements",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(fixtures.store_size_request()),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])
