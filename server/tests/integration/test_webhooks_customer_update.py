import random
import uuid

from server.database.database_manager import db
from server.database.models import User
from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures, WEBHOOK_SHOPIFY_ENDPOINT

CUSTOMERS_CREATE_REQUEST_HEADERS = {
    "X-Shopify-Topic": "customers/create",
}

CUSTOMERS_UPDATE_REQUEST_HEADERS = {
    "X-Shopify-Topic": "customers/update",
}


class TestWebhooksCustomerUpdate(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_webhook_without_topic_header(self):
        # when
        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, {}, {})

        # then
        self.assert400(response)

    def test_unsupported_webhook_type(self):
        # when
        response = self._post(
            WEBHOOK_SHOPIFY_ENDPOINT,
            {},
            {
                "X-Shopify-Topic": f"orders/{uuid.uuid4()}",
            },
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 0)

    def test_customers_create_event(self):
        # when
        webhook_customer = fixtures.webhook_customer_update(phone=random.randint(1000000000, 9999999999))
        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_customer, CUSTOMERS_CREATE_REQUEST_HEADERS)

        # then
        self.assert200(response)
        user = self.user_service.get_user_by_email(webhook_customer["email"])
        self.assertIsNotNone(user)
        self.assertEqual(user.email, webhook_customer["email"])
        self.assertEqual(user.phone_number, str(webhook_customer["phone"]))
        self.assertEqual(user.first_name, webhook_customer["first_name"])
        self.assertEqual(user.last_name, webhook_customer["last_name"])
        self.assertEqual(user.shopify_id, str(webhook_customer["id"]))
        self.assertEqual(user.account_status, webhook_customer["state"] == "enabled")

    def test_customers_update_event(self):
        # given
        user = self.user_service.create_user(
            fixtures.create_user_request(
                shopify_id=str(random.randint(1000, 1000000)), phone_number=utils.generate_phone_number()
            )
        )

        # when
        webhook_customer = fixtures.webhook_customer_update(
            shopify_id=int(user.shopify_id),
            email=f"new-{user.email}",
            phone=random.randint(1000000000, 9999999999),
            account_status=not user.account_status,
        )
        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_customer, CUSTOMERS_UPDATE_REQUEST_HEADERS)

        # then
        self.assert200(response)
        user = self.user_service.get_user_by_email(webhook_customer["email"])

        self.assertIsNotNone(user)
        self.assertEqual(user.email, webhook_customer["email"])
        self.assertEqual(user.phone_number, str(webhook_customer["phone"]))
        self.assertEqual(user.first_name, webhook_customer["first_name"])
        self.assertEqual(user.last_name, webhook_customer["last_name"])
        self.assertEqual(user.shopify_id, str(webhook_customer["id"]))
        self.assertEqual(user.account_status, webhook_customer["state"] == "enabled")

    def test_customers_update_event_user_phone_from_default_address(self):
        # given
        user = self.user_service.create_user(
            fixtures.create_user_request(
                shopify_id=str(random.randint(1000, 1000000)), phone_number=utils.generate_phone_number()
            )
        )

        # when
        new_phone_number = str(random.randint(1000000000, 9999999999))
        webhook_customer = fixtures.webhook_customer_update(
            shopify_id=int(user.shopify_id),
            email=f"new-{user.email}",
            phone=None,
            account_status=not user.account_status,
            default_address={"phone": new_phone_number},
        )
        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_customer, CUSTOMERS_UPDATE_REQUEST_HEADERS)

        # then
        self.assert200(response)
        user = self.user_service.get_user_by_email(webhook_customer["email"])

        self.assertIsNotNone(user)
        self.assertEqual(user.email, webhook_customer["email"])
        self.assertEqual(user.phone_number, new_phone_number)
        self.assertEqual(user.first_name, webhook_customer["first_name"])
        self.assertEqual(user.last_name, webhook_customer["last_name"])
        self.assertEqual(user.shopify_id, str(webhook_customer["id"]))
        self.assertEqual(user.account_status, webhook_customer["state"] == "enabled")

    def test_customers_update_customer_by_email_with_shopify_id(self):
        # given
        shopify_id = random.randint(1000000000, 9999999999)
        create_user = fixtures.create_user_request(shopify_id=str(shopify_id))
        db_user = User(
            first_name=create_user.first_name,
            last_name=create_user.last_name,
            email=create_user.email,
            shopify_id=create_user.shopify_id,
            account_status=True,
        )

        db.session.add(db_user)
        db.session.commit()
        db.session.refresh(db_user)

        # when
        webhook_customer = fixtures.webhook_customer_update(shopify_id=shopify_id, email=f"{db_user.email}")
        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_customer, CUSTOMERS_UPDATE_REQUEST_HEADERS)

        # then
        self.assert200(response)
        user = self.user_service.get_user_by_email(webhook_customer["email"])

        self.assertIsNotNone(user)
        self.assertEqual(user.email, webhook_customer["email"])
        self.assertEqual(user.first_name, webhook_customer["first_name"])
        self.assertEqual(user.last_name, webhook_customer["last_name"])
        self.assertEqual(user.shopify_id, create_user.shopify_id)

    def test_customers_disable_event(self):
        # given
        user = self.user_service.create_user(
            fixtures.create_user_request(shopify_id=str(random.randint(1000, 1000000)), account_status=True)
        )

        # when
        webhook_customer = fixtures.webhook_customer_update(
            shopify_id=int(user.shopify_id),
            email=user.email,
            account_status=False,
        )
        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_customer, CUSTOMERS_UPDATE_REQUEST_HEADERS)

        # then
        self.assert200(response)
        user = self.user_service.get_user_by_email(webhook_customer["email"])

        self.assertIsNotNone(user)
        self.assertEqual(user.account_status, False)

    def test_customers_enable_event(self):
        # given
        user = self.user_service.create_user(
            fixtures.create_user_request(shopify_id=str(random.randint(1000, 1000000)), account_status=False)
        )

        # when
        webhook_customer = fixtures.webhook_customer_update(
            shopify_id=int(user.shopify_id),
            email=user.email,
            account_status=True,
        )
        response = self._post(WEBHOOK_SHOPIFY_ENDPOINT, webhook_customer, CUSTOMERS_UPDATE_REQUEST_HEADERS)

        # then
        self.assert200(response)
        user = self.user_service.get_user_by_email(webhook_customer["email"])

        self.assertIsNotNone(user)
        self.assertEqual(user.account_status, True)
