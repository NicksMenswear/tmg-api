from __future__ import absolute_import

import json
import random
import unittest
import uuid

from server.database.models import User
from server.test import BaseTestCase


class TestUsers(BaseTestCase):
    def setUp(self):
        super(TestUsers, self).setUp()

        self.db = self.session()
        self.db.query(User).delete()
        self.db.commit()
        self.request_headers = {
            "Accept": "application/json",
        }

    @staticmethod
    def create_db_user(id=None, first_name=None, last_name=None, email=None, shopify_id=None, account_status=True):
        return User(
            id=str(uuid.uuid4()) if id is None else id,
            first_name=first_name if first_name is not None else str(uuid.uuid4()),
            last_name=last_name if last_name is not None else str(uuid.uuid4()),
            email=email if email is not None else f"{str(uuid.uuid4())}@example.com",
            shopify_id=shopify_id if shopify_id is not None else str(random.randint(1000, 100000)),
            account_status=account_status,
        )

    @staticmethod
    def create_request_user(first_name=None, last_name=None, email=None, account_status=True):
        return {
            "first_name": first_name if first_name is not None else str(uuid.uuid4()),
            "last_name": last_name if last_name is not None else str(uuid.uuid4()),
            "email": email if email is not None else f"{str(uuid.uuid4())}@example.com",
            "account_status": account_status,
        }

    def assert_response_user_with_db_user(self, user: User, response_user: dict):
        self.assertEqual(response_user["id"], str(user.id))
        self.assertEqual(response_user["first_name"], user.first_name)
        self.assertEqual(response_user["last_name"], user.last_name)
        self.assertEqual(response_user["email"], user.email)
        self.assertEqual(response_user["shopify_id"], user.shopify_id)
        self.assertEqual(response_user["account_status"], user.account_status)

    def test_get_non_existing_user_by_email(self):
        response = self.client.open(
            "/users/{email}".format(email=f"{str(uuid.uuid4())}@example.com"),
            query_string=self.hmac_query_params,
            method="GET",
            content_type="application/json",
        )

        self.assert404(response)

    @unittest.skip("this should fail on validation phase")
    def test_get_user_not_an_email_id(self):
        response = self.client.open(
            "/users/{email}".format(email="not-an-email"), query_string=self.hmac_query_params, method="GET"
        )

        self.assert400(response)

    def test_get_existing_user_by_email(self):
        # given
        user = self.create_db_user(email="existing@example.com")
        self.db.add(user)
        self.db.commit()

        # when
        response = self.client.open(
            "/users/{email}".format(email="existing@example.com"), query_string=self.hmac_query_params, method="GET"
        )

        # then
        self.assert200(response)
        self.assert_response_user_with_db_user(user, response.json)

    def test_create_user(self):
        # given
        user = self.create_request_user()

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(user),
            headers=self.request_headers,
            content_type="application/json",
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(response.json["first_name"], user["first_name"])
        self.assertEqual(response.json["last_name"], user["last_name"])
        self.assertEqual(response.json["email"], user["email"])
        self.assertEqual(response.json["account_status"], user["account_status"])
        self.assertIsNotNone(response.json["id"])
        self.assertIsNotNone(response.json["shopify_id"])

    def test_create_user_without_email(self):
        # given
        user = self.create_request_user()
        del user["email"]

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(user),
            headers=self.request_headers,
            content_type="application/json",
        )

        # then
        self.assertStatus(response, 400)

    def test_get_list_of_users_from_empty_db(self):
        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type="application/json",
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_list_of_users(self):
        # given
        user1 = self.create_db_user()
        user2 = self.create_db_user()
        self.db.add(user1)
        self.db.add(user2)
        self.db.commit()

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type="application/json",
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assert_response_user_with_db_user(user1, response.json[0])
        self.assert_response_user_with_db_user(user2, response.json[1])

    def test_update_user_with_non_existing_email(self):
        # given
        user = self.create_request_user()

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(user),
            headers=self.request_headers,
            content_type="application/json",
        )

        # then
        self.assert404(response)

    def test_update_user(self):
        # given
        user = self.create_db_user()
        self.db.add(user)
        self.db.commit()

        # when
        new_first_name = user.first_name + "-updated"
        new_last_name = user.last_name + "-updated"
        new_account_status = not user.account_status
        new_shopify_id = str(random.randint(1000, 100000))

        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(
                {
                    "first_name2": new_first_name,
                    "last_name2": new_last_name,
                    "email2": user.email,
                    "shopify_id2": new_shopify_id,
                    "account_status2": new_account_status,
                }
            ),
            headers=self.request_headers,
            content_type="application/json",
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json["first_name"], new_first_name)
        self.assertEqual(response.json["last_name"], new_last_name)
        self.assertEqual(response.json["email"], user.email)
        self.assertEqual(response.json["account_status"], new_account_status)
        self.assertEqual(response.json["id"], str(user.id))
        self.assertEqual(response.json["shopify_id"], new_shopify_id)

    def test_update_user_missing_required_fields(self):
        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps({}),
            headers=self.request_headers,
            content_type="application/json",
        )

        # then
        self.assert400(response)


if __name__ == "__main__":
    unittest.main()
