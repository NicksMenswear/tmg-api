from server.tests.integration import BaseTestCase


class TestJobE2ECleanUp(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_e2e_clean_up(self):
        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            query_string={},
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        self.assertStatus(response, 200)
