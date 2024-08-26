from server.tests.integration import BaseTestCase


class TestEvents(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_hello_world(self):
        response = self.client.open(
            "/jobs/hello-world",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        self.assertStatus(response, 200)
