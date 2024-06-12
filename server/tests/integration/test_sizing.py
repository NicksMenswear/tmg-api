import json

from server.tests.integration import BaseTestCase, fixtures


class TestSizing(BaseTestCase):
    def test_store_sizing(self):
        # when
        response = self.client.open(
            "/sizing",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(fixtures.store_sizing_request()),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])
