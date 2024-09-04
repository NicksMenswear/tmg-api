from server.tests.integration import BaseTestCase


class TestJobE2ECleanUp(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_e2e_clean_up(self):
        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        self.assertStatus(response, 200)
