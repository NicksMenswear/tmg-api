import uuid

from server.tests.integration import BaseTestCase, fixtures
from server.tests.utils import generate_email


class TestAuth(BaseTestCase):
    def test_login_user_not_found(self):
        # given
        user_email = generate_email()

        # when
        response = self.client.open(
            "/login",
            query_string={**self.hmac_query_params, "email": user_email},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_login_shopify_customer_not_found(self):
        # given
        user = self.app.user_service.create_user(
            fixtures.create_user_request(email=f"{uuid.uuid4()}@shopify-user-does-not-exists.com")
        )

        # when
        response = self.client.open(
            "/login",
            query_string={**self.hmac_query_params, "email": user.email},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_login_shopify_customer_with_state(self):
        # given
        inputs_outputs = [
            [{"email": generate_email(), "state": "enabled", "tags": ""}, {"state": "enabled"}],
            [{"email": generate_email(), "state": "disabled", "tags": ""}, {"state": "disabled"}],
            [
                {"email": generate_email(), "state": "disabled", "tags": "legacy"},
                {"state": "disabled", "is_legacy": True},
            ],
            [{"email": generate_email(), "state": "enabled", "tags": "legacy"}, {"state": "enabled"}],
            [
                {"email": generate_email(), "state": "disabled", "tags": "more-tags,legacy,even-more-tags"},
                {"state": "disabled", "is_legacy": True},
            ],
        ]

        for input_output in inputs_outputs:
            customer_email = input_output[0]["email"]
            user = self.app.user_service.create_user(fixtures.create_user_request(email=customer_email))
            shopify_service = self.app.shopify_service
            shopify_service.customers = {customer_email: input_output[0]}

            # when
            response = self.client.open(
                "/login",
                query_string={**self.hmac_query_params, "email": user.email},
                method="GET",
                headers=self.request_headers,
                content_type=self.content_type,
            )

            # then
            self.assertStatus(response, 200)
            self.assertEqual(response.json, input_output[1])
