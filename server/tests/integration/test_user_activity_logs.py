from __future__ import absolute_import

import json
import uuid

from server import encoder
from server.models.user_model import CreateUserModel
from server.tests.integration import BaseTestCase, fixtures


class TestUserActivityLogs(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_create_user(self):
        # when
        create_user: CreateUserModel = fixtures.create_user_request()

        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(create_user.model_dump(), cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(create_user.first_name, response.json["first_name"])
        self.assertEqual(create_user.last_name, response.json["last_name"])
        self.assertEqual(create_user.email, response.json["email"])
        self.assertIsNotNone(response.json["id"])

        self.assertTrue(uuid.UUID(response.json["id"]) in self.email_service.sent_activations)
