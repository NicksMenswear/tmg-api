from __future__ import absolute_import

import json
import uuid

from server import encoder
from server.database.models import Look
from server.services.attendee import AttendeeService
from server.services.event import EventService
from server.services.look import LookService
from server.services.role import RoleService
from server.services.user import UserService
from server.test import BaseTestCase, fixtures


class TestLooks(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.look_service = LookService()
        self.role_service = RoleService()
        self.user_service = UserService()
        self.attendee_service = AttendeeService()
        self.event_service = EventService()

    def assert_equal_response_look_with_db_look(self, look: Look, response_look: dict):
        self.assertEqual(response_look["id"], str(look.id))
        self.assertEqual(response_look["look_name"], look.look_name)
        self.assertEqual(response_look["user_id"], str(look.user_id))
        self.assertEqual(response_look["product_specs"], look.product_specs)

    def test_create_look(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())

        # when
        look_data = fixtures.look_request(user_id=user.id)

        response = self.client.open(
            "/looks",
            query_string=self.hmac_query_params,
            data=json.dumps(look_data, cls=encoder.CustomJSONEncoder),
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assert_equal_response_look_with_db_look(
            self.look_service.get_look_by_id(response.json["id"]), response.json
        )

    def test_create_look_duplicate(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        look = self.look_service.create_look(fixtures.look_request(user_id=user.id))

        # when
        look_data = fixtures.look_request(user_id=user.id, look_name=look.look_name)

        response = self.client.open(
            "/looks",
            query_string=self.hmac_query_params,
            data=json.dumps(look_data, cls=encoder.CustomJSONEncoder),
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 409)

    def test_get_non_existing_look_by_id(self):
        # when
        response = self.client.open(
            f"/looks/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_look_by_id(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        look = self.look_service.create_look(fixtures.look_request(user_id=user.id))

        # when
        response = self.client.open(
            f"/looks/{str(look.id)}",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assert_equal_response_look_with_db_look(look, response.json)

    def test_update_look_for_invalid_user(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        look = self.look_service.create_look(fixtures.look_request(user_id=user.id))

        # when
        look_data = fixtures.update_look_request(user_id=str(uuid.uuid4()))

        response = self.client.open(
            f"/looks/{look.id}",
            query_string=self.hmac_query_params,
            data=json.dumps(look_data, cls=encoder.CustomJSONEncoder),
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_update_look_for_invalid_look_id(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())

        # when
        look_data = fixtures.update_look_request(user_id=user.id)

        response = self.client.open(
            f"/looks/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            data=json.dumps(look_data, cls=encoder.CustomJSONEncoder),
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_update_look(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(fixtures.look_request(user_id=str(user.id)))
        role = self.role_service.create_role(fixtures.role_request(event_id=str(event.id)))
        self.attendee_service.create_attendee(
            fixtures.attendee_request(email=user.email, event_id=str(event.id), role=str(role.id), look_id=look.id)
        )

        # when
        look_data = fixtures.update_look_request(
            user_id=str(user.id),
            look_name=f"{str(uuid.uuid4())}-new_look_name",
        )

        response = self.client.open(
            f"/looks/{str(look.id)}",
            query_string=self.hmac_query_params,
            data=json.dumps(look_data, cls=encoder.CustomJSONEncoder),
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json["id"], str(look.id))

    def test_update_look_existing(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        look = self.look_service.create_look(fixtures.look_request(user_id=str(user.id)))
        look2 = self.look_service.create_look(fixtures.look_request(user_id=str(user.id)))
        role = self.role_service.create_role(fixtures.role_request(event_id=str(event.id)))
        self.attendee_service.create_attendee(
            fixtures.attendee_request(email=user.email, event_id=str(event.id), role=str(role.id), look_id=look.id)
        )

        # when
        look_data = fixtures.update_look_request(
            user_id=str(user.id),
            look_name=look2.look_name,
        )

        response = self.client.open(
            f"/looks/{str(look.id)}",
            query_string=self.hmac_query_params,
            data=json.dumps(look_data, cls=encoder.CustomJSONEncoder),
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 409)

    def test_get_empty_set_of_events_for_look(self):
        # when
        response = self.client.open(
            f"/looks/{str(uuid.uuid4())}/events",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_events_for_look(self):
        user1 = self.user_service.create_user(fixtures.user_request())
        user2 = self.user_service.create_user(fixtures.user_request())
        event1 = self.event_service.create_event(fixtures.event_request(user_id=user1.id))
        event2 = self.event_service.create_event(fixtures.event_request(user_id=user2.id))
        look = self.look_service.create_look(fixtures.look_request(user_id=str(user1.id)))
        self.attendee_service.create_attendee(
            fixtures.attendee_request(event_id=event1.id, email=user1.email, look_id=look.id)
        )
        self.attendee_service.create_attendee(
            fixtures.attendee_request(event_id=event2.id, email=user2.email, look_id=look.id)
        )

        # when
        response = self.client.open(
            f"/looks/{str(look.id)}/events",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assertEqual(response.json[0]["id"], str(event1.id))
        self.assertEqual(response.json[0]["event_name"], str(event1.event_name))
        self.assertEqual(response.json[1]["id"], str(event2.id))
        self.assertEqual(response.json[1]["event_name"], str(event2.event_name))

    def test_delete_look_non_existing(self):
        # when
        response = self.client.open(
            f"/looks/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="DELETE",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_delete_look(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        look = self.look_service.create_look(fixtures.look_request(user_id=user.id))

        # when
        response = self.client.open(
            f"/looks/{look.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 204)
        look_in_db = self.look_service.get_look_by_id(look.id)
        self.assertIsNone(look_in_db)
