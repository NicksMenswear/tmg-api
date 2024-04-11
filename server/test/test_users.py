from __future__ import absolute_import

import json
import random
import unittest
import uuid

from server import encoder
from server.database.models import User
from server.test import BaseTestCase, CONTENT_TYPE_JSON


class TestUsers(BaseTestCase):
    def setUp(self):
        super(TestUsers, self).setUp()

        self.db = self.session()
        self.db.query(User).delete()
        self.db.commit()
        self.request_headers = {
            "Accept": CONTENT_TYPE_JSON,
        }

    @staticmethod
    def create_db_user(**kwargs):
        return User(
            id=kwargs.get("id", str(uuid.uuid4())),
            first_name=kwargs.get("first_name", str(uuid.uuid4())),
            last_name=kwargs.get("last_name", str(uuid.uuid4())),
            email=kwargs.get("email", f"{str(uuid.uuid4())}@example.com"),
            shopify_id=kwargs.get("shopify_id", str(random.randint(1000, 100000))),
            account_status=kwargs.get("account_status", True),
        )

    @staticmethod
    def create_user_request_payload(**kwargs):
        return {
            "first_name": kwargs.get("first_name", str(uuid.uuid4())),
            "last_name": kwargs.get("last_name", str(uuid.uuid4())),
            "email": kwargs.get("email", f"{str(uuid.uuid4())}@example.com"),
            "account_status": kwargs.get("account_status", True),
        }

    def assert_equal_response_user_with_db_user(self, user: User, response_user: dict):
        self.assertEqual(response_user["id"], str(user.id))
        self.assertEqual(response_user["first_name"], user.first_name)
        self.assertEqual(response_user["last_name"], user.last_name)
        self.assertEqual(response_user["email"], user.email)
        self.assertEqual(response_user["shopify_id"], user.shopify_id)
        self.assertEqual(response_user["account_status"], user.account_status)

    def assert_equal_left(self, left, right):
        # Asserts that all key-value pairs in left are present and equal in right.
        for key in left:
            self.assertEqual(left[key], right[key])

    def test_get_non_existing_user_by_email(self):
        # when
        response = self.client.open(
            "/users/{email}".format(email=f"{str(uuid.uuid4())}@example.com"),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assert404(response)

    @unittest.skip("this should fail on validation phase")
    def test_get_user_not_an_email_id(self):
        # when
        response = self.client.open(
            "/users/{email}".format(email="not-an-email"), query_string=self.hmac_query_params, method="GET"
        )

        # then
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
        self.assert_equal_response_user_with_db_user(user, response.json)

    def test_create_user(self):
        # given
        user = self.create_user_request_payload()

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(user, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assertStatus(response, 201)
        self.assert_equal_left(user, response.json)
        self.assertIsNotNone(response.json["id"])
        self.assertIsNotNone(response.json["shopify_id"])

    def test_create_user_without_email(self):
        # given
        user = self.create_user_request_payload()
        del user["email"]

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(user, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=CONTENT_TYPE_JSON,
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
            content_type=CONTENT_TYPE_JSON,
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
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assert_equal_response_user_with_db_user(user1, response.json[0])
        self.assert_equal_response_user_with_db_user(user2, response.json[1])

    def test_update_user_with_non_existing_email(self):
        # given
        user = self.create_user_request_payload()

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(user, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assert404(response)

    def test_update_user(self):
        # given
        user = self.create_db_user()
        self.db.add(user)
        self.db.commit()

        # when
        updated_user = self.create_user_request_payload(
            first_name=user.first_name + "-updated",
            last_name=user.last_name + "-updated",
            email=user.email,
            account_status=not user.account_status,
        )
        updated_user["shopify_id"] = str(random.randint(1000, 100000))

        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(updated_user, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assert200(response)
        self.assert_equal_left(updated_user, response.json)

    def test_update_user_missing_required_fields(self):
        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps({}, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=CONTENT_TYPE_JSON,
        )

        # then
        self.assert400(response)
