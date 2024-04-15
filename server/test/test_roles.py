from __future__ import absolute_import

import json
import unittest
import uuid

from server import encoder
from server.database.models import Role
from server.services.event import EventService
from server.services.look import LookService
from server.services.role import RoleService
from server.services.user import UserService
from server.test import BaseTestCase, fixtures


class TestRoles(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.user_service = UserService(self.session_factory)
        self.look_service = LookService(self.session_factory)
        self.event_service = EventService(self.session_factory)
        self.role_service = RoleService(self.session_factory)

    def assert_equal_response_role_with_db_role(self, role: Role, response_role: dict):
        self.assertEqual(response_role["id"], str(role.id))
        self.assertEqual(response_role["role_name"], role.role_name)
        self.assertEqual(response_role["event_id"], str(role.event_id))
        self.assertEqual(response_role["look_id"], str(role.look_id))

    def test_get_list_of_all_roles_from_empty_db(self):
        # when
        response = self.client.open(
            "/roles",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_list_of_all_roles(self):
        # given
        user1 = self.user_service.create_user(**fixtures.user_request())
        user2 = self.user_service.create_user(**fixtures.user_request())
        event1 = self.event_service.create_event(**fixtures.event_request(email=user1.email))
        event2 = self.event_service.create_event(**fixtures.event_request(email=user2.email))
        look1 = self.look_service.create_look(**fixtures.look_request(event_id=event1.id, user_id=user1.id))
        look2 = self.look_service.create_look(**fixtures.look_request(event_id=event2.id, user_id=user2.id))
        role1 = self.role_service.create_role(**fixtures.role_request(event_id=event1.id, look_id=look1.id))
        role2 = self.role_service.create_role(**fixtures.role_request(event_id=event1.id, look_id=look2.id))
        role3 = self.role_service.create_role(**fixtures.role_request(event_id=event2.id, look_id=look1.id))

        # when
        response = self.client.open(
            "/roles",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 3)
        self.assert_equal_response_role_with_db_role(role1, response.json[0])
        self.assert_equal_response_role_with_db_role(role2, response.json[1])
        self.assert_equal_response_role_with_db_role(role3, response.json[2])

    def test_create_role(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        look = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))

        # when
        role = fixtures.role_request(event_id=str(event.id), look_id=str(look.id))

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
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        look = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))

        # when
        role = fixtures.role_request(event_id=str(uuid.uuid4()), look_id=str(look.id))

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

    def test_create_role_look_not_found(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))

        # when
        role = fixtures.role_request(event_id=str(event.id), look_id=str(uuid.uuid4()))

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

    @unittest.skip("Review this later")
    def test_create_role_with_same_name_as_existing(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        look = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))
        role = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look.id))

        # when
        role = fixtures.role_request(event_id=str(event.id), look_id=str(look.id), role_name=role.role_name)

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
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        look = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))
        role = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look.id))

        # when
        query_params = {**self.hmac_query_params, "role_id": str(role.id), "event_id": str(event.id)}

        response = self.client.open(
            f"/roles_with_roleid_eventid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assert_equal_response_role_with_db_role(role, response.json)

    def test_get_role_by_id_not_found(self):
        # when
        query_params = {**self.hmac_query_params, "role_id": str(uuid.uuid4()), "event_id": str(uuid.uuid4())}

        response = self.client.open(
            f"/roles_with_roleid_eventid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_get_roles_by_event_id(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        look = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))
        role1 = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look.id))
        role2 = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look.id))

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
        self.assertStatus(response, 404)

    def test_get_roles_for_event_without_roles(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))

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

    def test_get_roles_with_look(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        look = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))
        role1 = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look.id))
        role2 = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look.id))

        # when
        query_params = {**self.hmac_query_params, "event_id": str(event.id)}

        response = self.client.open(
            f"/event_roles_with_look",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        data = response.json
        self.assertEqual(len(data.get("all_looks")), 1)
        self.assertEqual(len(data.get("role_details")), 2)
        self.assertEqual(data["all_looks"][0]["look_id"], str(look.id))
        self.assertEqual(data["all_looks"][0]["look_name"], str(look.look_name))
        self.assertEqual(data["role_details"][0]["event_id"], str(event.id))
        self.assertEqual(data["role_details"][0]["role_id"], str(role1.id))
        self.assertEqual(data["role_details"][0]["role_name"], role1.role_name)
        self.assertEqual(data["role_details"][0]["look_data"]["look_id"], str(look.id))
        self.assertEqual(data["role_details"][0]["look_data"]["look_name"], str(look.look_name))
        self.assertEqual(data["role_details"][1]["event_id"], str(event.id))
        self.assertEqual(data["role_details"][1]["role_id"], str(role2.id))
        self.assertEqual(data["role_details"][1]["role_name"], str(role2.role_name))
        self.assertEqual(data["role_details"][1]["look_data"]["look_id"], str(look.id))
        self.assertEqual(data["role_details"][1]["look_data"]["look_name"], str(look.look_name))

    def test_get_roles_without_looks(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))

        # when
        query_params = {**self.hmac_query_params, "event_id": str(event.id)}

        response = self.client.open(
            f"/event_roles_with_look",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        data = response.json
        self.assertEqual(len(data.get("all_looks")), 0)
        self.assertEqual(len(data.get("role_details")), 0)

    def test_update_role(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(email=user.email))
        look = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))
        role = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look.id))

        # when
        new_role_name = role.role_name + "-updated"

        role_data = {
            "role_name": role.role_name,
            "new_role_name": new_role_name,
            "look_id": str(look.id),
        }

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
        self.assertEqual(response.json["look_id"], str(look.id))
        self.assertEqual(response.json["event_id"], str(event.id))
