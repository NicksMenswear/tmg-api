from __future__ import absolute_import

import json
import uuid

from server import encoder
from server.services.attendee import AttendeeService
from server.services.event import EventService
from server.services.look import LookService
from server.services.role import RoleService
from server.services.user import UserService
from server.test import BaseTestCase, fixtures


class TestAttendees(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.attendee_service = AttendeeService(self.session_factory)
        self.user_service = UserService(self.session_factory)
        self.event_service = EventService(self.session_factory)
        self.look_service = LookService(self.session_factory)
        self.role_service = RoleService(self.session_factory)

    def assert_equal_attendee(self, attendee_request, attendee_response):
        self.assertEqual(str(attendee_request["event_id"]), attendee_response["event_id"])
        self.assertEqual(attendee_request["invite"], attendee_response["invite"])
        self.assertEqual(attendee_request["pay"], attendee_response["pay"])
        self.assertEqual(attendee_request["size"], attendee_response["size"])
        self.assertEqual(attendee_request["style"], attendee_response["style"])
        self.assertEqual(attendee_request["ship"], attendee_response["ship"])
        self.assertEqual(str(attendee_request["role"]), str(attendee_response["role"]))
        self.assertIsNotNone(attendee_response["attendee_id"])

    def test_create_attendee_without_role(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(user_id=user.id))

        # when
        attendee = fixtures.attendee_request(event_id=event.id, role=None)

        response = self.client.open(
            "/event_attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(attendee, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNone(response.json["role"])
        self.assertNotEqual(str(user.id), response.json["attendee_id"])
        self.assert_equal_attendee(attendee, response.json)
        attendee_user = self.user_service.get_user_by_email(attendee["email"])
        self.assertEqual(str(attendee_user.id), response.json["attendee_id"])
        self.assertEqual(attendee_user.first_name, attendee["first_name"])
        self.assertEqual(attendee_user.last_name, attendee["last_name"])
        self.assertEqual(attendee_user.email, attendee["email"])
        self.assertFalse(attendee_user.account_status)
        self.assertTrue(response.json["is_active"])

    def test_create_attendee_with_role(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))
        role = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look.id))

        # when
        attendee = fixtures.attendee_request(event_id=event.id, role=role.id)

        response = self.client.open(
            "/event_attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(attendee, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["role"])
        self.assertNotEqual(str(user.id), response.json["attendee_id"])
        self.assert_equal_attendee(attendee, response.json)
        attendee_user = self.user_service.get_user_by_email(attendee["email"])
        self.assertEqual(str(attendee_user.id), response.json["attendee_id"])
        self.assertEqual(attendee_user.first_name, attendee["first_name"])
        self.assertEqual(attendee_user.last_name, attendee["last_name"])
        self.assertEqual(attendee_user.email, attendee["email"])
        self.assertFalse(attendee_user.account_status)
        self.assertTrue(response.json["is_active"])

    def test_create_attendee_for_existing_attendee_user(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))
        role = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look.id))
        attendee_user = self.user_service.create_user(**fixtures.user_request())

        # when
        attendee = fixtures.attendee_request(
            event_id=event.id,
            role=role.id,
            email=attendee_user.email,
            first_name=attendee_user.first_name,
            last_name=attendee_user.last_name,
        )

        response = self.client.open(
            "/event_attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(attendee, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["role"])
        self.assertNotEqual(str(user.id), response.json["attendee_id"])
        self.assert_equal_attendee(attendee, response.json)
        self.assertEqual(str(attendee_user.id), response.json["attendee_id"])
        self.assertEqual(attendee_user.first_name, attendee["first_name"])
        self.assertEqual(attendee_user.last_name, attendee["last_name"])
        self.assertEqual(attendee_user.email, attendee["email"])

    def test_create_attendee_but_it_already_exist_and_associated(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(**fixtures.user_request())
        self.attendee_service.create_attendee(**fixtures.attendee_request(event_id=event.id, email=attendee_user.email))

        # when
        new_attendee = fixtures.attendee_request(
            event_id=event.id,
            email=attendee_user.email,
            first_name=attendee_user.first_name,
            last_name=attendee_user.last_name,
        )

        response = self.client.open(
            "/event_attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(new_attendee, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 409)

    def test_get_attendee_event_non_existing_user(self):
        # when
        query_params = {
            **self.hmac_query_params,
            "email": f"{str(uuid.uuid4())}@example.com",
            "event_id": str(uuid.uuid4()),
        }

        response = self.client.open(
            "/event_attendees",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_get_attendee_event(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(user_id=user.id))
        attendee = self.attendee_service.create_attendee(
            **fixtures.attendee_request(event_id=event.id, email=user.email)
        )

        # when
        query_params = {**self.hmac_query_params, "email": user.email, "event_id": event.id}

        response = self.client.open(
            "/event_attendees",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(str(event.id), response.json["id"])
        self.assertEqual(str(attendee.attendee_id), response.json["user_id"])

    def test_get_attendee_event_for_not_active_event(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(user_id=user.id, is_active=False))
        attendee = self.attendee_service.create_attendee(
            **fixtures.attendee_request(event_id=event.id, email=user.email)
        )

        # when
        query_params = {**self.hmac_query_params, "email": user.email, "event_id": event.id}

        response = self.client.open(
            "/event_attendees",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_get_attendee_event_for_not_active_attendee(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(user_id=user.id))
        attendee = self.attendee_service.create_attendee(
            **fixtures.attendee_request(event_id=event.id, email=user.email, is_active=False)
        )

        # when
        query_params = {**self.hmac_query_params, "email": user.email, "event_id": event.id}

        response = self.client.open(
            "/event_attendees",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_update_attendee(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(user_id=user.id))
        look1 = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))
        role1 = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look1.id))
        look2 = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))
        role2 = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look2.id))
        attendee = self.attendee_service.create_attendee(
            **fixtures.attendee_request(
                event_id=event.id, email=user.email, style=1, invite=2, pay=3, size=4, ship=5, role=str(role1.id)
            )
        )

        # when
        updated_attendee_data = {
            "email": user.email,
            "event_id": event.id,
            "style": attendee.style + 10,
            "invite": attendee.invite + 10,
            "pay": attendee.pay + 10,
            "size": attendee.size + 10,
            "ship": attendee.ship + 10,
            "role": str(role2.id),
        }

        response = self.client.open(
            "/event_attendees",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(updated_attendee_data, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)

        # checking response
        self.assert_equal_attendee(updated_attendee_data, response.json)

        # checking db
        updated_attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertEqual(updated_attendee_data["style"], updated_attendee.style)
        self.assertEqual(updated_attendee_data["invite"], updated_attendee.invite)
        self.assertEqual(updated_attendee_data["pay"], updated_attendee.pay)
        self.assertEqual(updated_attendee_data["size"], updated_attendee.size)
        self.assertEqual(updated_attendee_data["ship"], updated_attendee.ship)
        self.assertEqual(str(role2.id), str(updated_attendee.role))

    def test_update_attendee_user_invalid(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(user_id=user.id))

        # when
        updated_attendee_data = {
            "email": f"{str(uuid.uuid4())}@example.com",
            "event_id": str(event.id),
            "style": 1,
            "invite": 2,
            "pay": 3,
            "size": 4,
            "ship": 5,
            "role": None,
        }

        response = self.client.open(
            "/event_attendees",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(updated_attendee_data, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_update_attendee_invalid_event(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())

        # when
        updated_attendee_data = {
            "email": user.email,
            "event_id": str(uuid.uuid4()),
            "style": 1,
            "invite": 2,
            "pay": 3,
            "size": 4,
            "ship": 5,
            "role": None,
        }

        response = self.client.open(
            "/event_attendees",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(updated_attendee_data, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_get_all_attendees_for_event(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))
        role = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look.id))
        attendee_user1 = self.user_service.create_user(**fixtures.user_request())
        attendee_user2 = self.user_service.create_user(**fixtures.user_request())
        attendee_user3 = self.user_service.create_user(**fixtures.user_request())
        attendee1 = self.attendee_service.create_attendee(
            **fixtures.attendee_request(event_id=event.id, email=attendee_user1.email, role=str(role.id))
        )
        attendee2 = self.attendee_service.create_attendee(
            **fixtures.attendee_request(event_id=event.id, email=attendee_user2.email, role=str(role.id))
        )
        self.attendee_service.create_attendee(
            **fixtures.attendee_request(
                event_id=event.id, email=attendee_user3.email, role=str(role.id), is_active=False
            )
        )

        # when
        query_params = {**self.hmac_query_params, "event_id": event.id}

        response = self.client.open(
            "/event_attendees_by_eventid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assertEqual(str(attendee1.id), response.json[0]["id"])
        self.assertEqual(str(attendee2.id), response.json[1]["id"])

    def test_get_all_attendees_for_invalid_event(self):
        # when
        query_params = {**self.hmac_query_params, "event_id": str(uuid.uuid4())}

        response = self.client.open(
            "/event_attendees_by_eventid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_deactivate_attendee(self):
        # given
        user = self.user_service.create_user(**fixtures.user_request())
        event = self.event_service.create_event(**fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(**fixtures.look_request(event_id=event.id, user_id=user.id))
        role = self.role_service.create_role(**fixtures.role_request(event_id=event.id, look_id=look.id))
        attendee = self.attendee_service.create_attendee(
            **fixtures.attendee_request(event_id=event.id, email=user.email, role=str(role.id))
        )

        # when
        response = self.client.open(
            "/delete_event_attendee",
            query_string=self.hmac_query_params,
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                {
                    "email": user.email,
                    "event_id": event.id,
                    "attendee_id": attendee.id,
                    "is_active": False,
                },  # TODO: we have bug here, likely in UI as well
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 204)

        # checking db
        soft_deleted_attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertEqual(False, soft_deleted_attendee.is_active)
