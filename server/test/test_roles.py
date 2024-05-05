from __future__ import absolute_import

import json
import uuid

from server import encoder
from server.database.models import Role
from server.services.event import EventService
from server.services.role import RoleService
from server.services.user import UserService
from server.test import BaseTestCase, fixtures


class TestRoles(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.user_service = UserService()
        self.event_service = EventService()
        self.role_service = RoleService()

    def assert_equal_response_role_with_db_role(self, role: Role, response_role: dict):
        self.assertEqual(response_role["id"], str(role.id))
        self.assertEqual(response_role["role_name"], role.role_name)
        self.assertEqual(response_role["event_id"], str(role.event_id))

    def test_create_role(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))

        # when
        role = fixtures.role_request(event_id=str(event.id))

        response = self.client.open(
            "/roles",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(role, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 201)
        self.assert_equal_left(role, response.json)

    def test_create_role_event_not_found(self):
        # when
        role = fixtures.role_request(event_id=str(uuid.uuid4()))

        response = self.client.open(
            "/roles",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(role, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 404)

    def test_create_role_with_same_name_as_existing(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.role_request(event_id=event.id))

        # when
        role = fixtures.role_request(event_id=str(event.id), role_name=role.role_name)

        response = self.client.open(
            "/roles",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(role, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 409)

    def test_get_role_by_id(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.role_request(event_id=event.id))

        # when
        response = self.client.open(
            f"/roles/{role.id}",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assert_equal_response_role_with_db_role(role, response.json)

    def test_get_role_by_id_not_found(self):
        # when
        response = self.client.open(
            f"/roles/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_get_roles_by_event_id(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        role1 = self.role_service.create_role(fixtures.role_request(event_id=event.id))
        role2 = self.role_service.create_role(fixtures.role_request(event_id=event.id))

        # when
        query_params = {**self.hmac_query_params, "event_id": str(event.id)}

        response = self.client.open(
            f"/roles_with_eventid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assert_equal_response_role_with_db_role(role1, response.json[0])
        self.assert_equal_response_role_with_db_role(role2, response.json[1])

    def test_get_roles_by_non_existing_event_id(self):
        # when
        query_params = {**self.hmac_query_params, "event_id": str(uuid.uuid4())}

        response = self.client.open(
            f"/roles_with_eventid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 0)

    def test_get_roles_for_event_without_roles(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))

        # when
        query_params = {**self.hmac_query_params, "event_id": str(event.id)}

        response = self.client.open(
            f"/roles_with_eventid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_update_role(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.role_request(event_id=event.id))

        # when
        new_role_name = role.role_name + "-updated"

        role_data = {"role_name": role.role_name, "new_role_name": new_role_name}

        response = self.client.open(
            "/roles",
            query_string=self.hmac_query_params,
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(role_data, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json["id"], str(role.id))
        self.assertEqual(response.json["role_name"], new_role_name)
        self.assertEqual(response.json["event_id"], str(event.id))
