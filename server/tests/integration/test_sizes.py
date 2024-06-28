import json

from server.tests.integration import BaseTestCase, fixtures


class TestSizes(BaseTestCase):
    def test_create_sizes(self):
        # when
        response = self.client.open(
            "/sizes",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(fixtures.store_size_request()),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])
