from __future__ import absolute_import

from server.database.models import Role
from server.services.event import EventService
from server.services.look import LookService
from server.services.role import RoleService
from server.services.user import UserService
from server.test import BaseTestCase
from server.test.fixtures import (
    create_user_request_payload,
    create_event_request_payload,
    create_look_request_payload,
    create_role_request_payload,
)


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
        user1 = self.user_service.create_user(**create_user_request_payload())
        user2 = self.user_service.create_user(**create_user_request_payload())
        event1 = self.event_service.create_event(**create_event_request_payload(user_id=user1.id))
        event2 = self.event_service.create_event(**create_event_request_payload(user_id=user2.id))
        look1 = self.look_service.create_look(**create_look_request_payload(event_id=event1.id, user_id=user1.id))
        look2 = self.look_service.create_look(**create_look_request_payload(event_id=event2.id, user_id=user2.id))
        role1 = self.role_service.create_role(**create_role_request_payload(event_id=event1.id, look_id=look1.id))
        role2 = self.role_service.create_role(**create_role_request_payload(event_id=event1.id, look_id=look2.id))
        role3 = self.role_service.create_role(**create_role_request_payload(event_id=event2.id, look_id=look1.id))

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
