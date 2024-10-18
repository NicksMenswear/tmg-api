import random
import uuid

from parameterized import parameterized

from server.models.shopify_model import ShopifyCustomer
from server.services.integrations.shopify_service import ShopifyService
from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures


class TestAuth(BaseTestCase):
    def test_login_user_not_found(self):
        # given
        user_email = utils.generate_email()

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

    @parameterized.expand(
        [
            [utils.generate_email(), "enabled", "", "enabled", False],
            [utils.generate_email(), "disabled", "", "disabled", False],
            [utils.generate_email(), "disabled", "legacy", "disabled", True],
            [utils.generate_email(), "enabled", "legacy", "enabled", False],
            [utils.generate_email(), "disabled", "more-tags,legacy,even-more-tags", "disabled", True],
        ]
    )
    def test_login_shopify_customer_with_state(
        self,
        input_email: str,
        input_state: str,
        input_tags: str,
        expected_state: str,
        expected_is_legacy: bool,
    ):
        shopify_service = self.app.shopify_service

        user = self.app.user_service.create_user(fixtures.create_user_request(email=input_email))
        shopify_customer = ShopifyCustomer(
            gid=ShopifyService.customer_gid(random.randint(10000, 10000000)),
            email=input_email,
            first_name="John",
            last_name="Doe",
            state=input_state,
            tags=input_tags.split(","),
        )
        shopify_service.customers[shopify_customer.gid] = shopify_customer

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
        self.assertEqual(response.json.get("state"), expected_state)
        self.assertEqual(response.json.get("is_legacy", False), expected_is_legacy)
