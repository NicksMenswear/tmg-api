from __future__ import absolute_import

import json
import random
import unittest
import uuid

from server import encoder
from server.database.models import User
from server.services.user import UserService
from server.test import BaseTestCase
from server.test.fixtures import create_user_request_payload


class TestUsers(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.user_service = UserService(self.session_factory)

    def assert_equal_response_user_with_db_user(self, user: User, response_user: dict):
        self.assertEqual(response_user["id"], str(user.id))
        self.assertEqual(response_user["first_name"], user.first_name)
        self.assertEqual(response_user["last_name"], user.last_name)
        self.assertEqual(response_user["email"], user.email)
        self.assertEqual(response_user["shopify_id"], user.shopify_id)
        self.assertEqual(response_user["account_status"], user.account_status)

    def test_get_non_existing_user_by_email(self):
        # when
        response = self.client.open(
            "/users/{email}".format(email=f"{str(uuid.uuid4())}@example.com"),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
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
        email = f"{str(uuid.uuid4())}@example.com"
        user = self.user_service.create_user(**create_user_request_payload(email=email))

        # when
        response = self.client.open(
            "/users/{email}".format(email=email), query_string=self.hmac_query_params, method="GET"
        )

        # then
        self.assert200(response)
        self.assert_equal_response_user_with_db_user(user, response.json)

    def test_create_user(self):
        # when
        user = create_user_request_payload()

        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(user, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assert_equal_left(user, response.json)
        self.assertIsNotNone(response.json["id"])
        self.assertIsNotNone(response.json["shopify_id"])

    def test_create_user_without_email(self):
        # when
        user = create_user_request_payload()
        del user["email"]

        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(user, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
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
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_list_of_users(self):
        # given
        user1 = self.user_service.create_user(**create_user_request_payload())
        user2 = self.user_service.create_user(**create_user_request_payload())

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assert_equal_response_user_with_db_user(user1, response.json[0])
        self.assert_equal_response_user_with_db_user(user2, response.json[1])

    def test_update_user_with_non_existing_email(self):
        # when
        user = create_user_request_payload()

        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(user, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_update_user(self):
        # given
        user = self.user_service.create_user(**create_user_request_payload())

        # when
        updated_user = create_user_request_payload(
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
            content_type=self.content_type,
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
            content_type=self.content_type,
        )

        # then
        self.assert400(response)
