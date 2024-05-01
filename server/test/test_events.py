from __future__ import absolute_import

import json
import uuid
from datetime import datetime

from server import encoder
from server.database.models import Event
from server.services.attendee import AttendeeService
from server.services.event import EventService
from server.services.look import LookService
from server.services.role import RoleService
from server.services.user import UserService
from server.test import BaseTestCase, fixtures


class TestEvents(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.user_service = UserService()
        self.event_service = EventService()
        self.look_service = LookService()
        self.attendee_service = AttendeeService()
        self.role_service = RoleService()

    def assert_equal_response_event_with_db_event(self, event: Event, response_event: dict):
        self.assertEqual(response_event["id"], str(event.id))
        self.assertEqual(response_event["event_name"], event.event_name)
        self.assertEqual(response_event["event_date"], str(event.event_date))
        self.assertEqual(response_event["user_id"], str(event.user_id))
        self.assertEqual(response_event["is_active"], event.is_active)

    def test_get_events_for_non_existing_user_by_email(self):
        # when
        response = self.client.open(
            "/events/{email}".format(email=f"{str(uuid.uuid4())}@example.com"),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_get_empty_list_of_events_by_user_email(self):
        # given
        email = f"{str(uuid.uuid4())}@example.com"
        self.user_service.create_user(fixtures.user_request(email=email))

        # when
        response = self.client.open(
            "/events/{email}".format(email=email),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json, [])

    def test_get_list_of_2_events_by_user_email_but_only_1_active(self):
        # given
        email = f"{str(uuid.uuid4())}@example.com"
        user = self.user_service.create_user(fixtures.user_request(email=email))

        self.event_service.create_event(fixtures.event_request(email=user.email, is_active=False))
        active_event = self.event_service.create_event(fixtures.event_request(email=user.email, is_active=True))

        # when
        response = self.client.open(
            "/events/{email}".format(email=email),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 1)
        self.assert_equal_response_event_with_db_event(active_event, response.json[0])

    def test_create_event_for_non_existing_user(self):
        # when
        response = self.client.open(
            "/events",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(fixtures.event_request(), cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assert404(response)

    def test_create_event_duplicate(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(email=user.email))

        # when
        response = self.client.open(
            "/events",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                fixtures.event_request(event_name=event.event_name, email=user.email, is_active=True),
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 409)

    def test_create_event(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())

        # when
        event_request = fixtures.event_request(email=user.email)

        response = self.client.open(
            "/events",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(event_request, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 201)
        self.assert_equal_response_event_with_db_event(
            self.event_service.get_event_by_id(response.json["id"]), response.json
        )

    def test_get_events_for_user_by_email(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(email=user.email))

        # when
        response = self.client.open(
            "/events/{email}".format(email=user.email),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 1)
        self.assert_equal_response_event_with_db_event(event, response.json[0])

    def test_update_event(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(email=user.email))

        # when
        response = self.client.open(
            "/events",
            query_string=self.hmac_query_params,
            method="PUT",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                fixtures.update_event_request(id=event.id, user_id=user.id, event_date=datetime.now().isoformat()),
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert200(response)
        self.assert_equal_response_event_with_db_event(self.event_service.get_event_by_id(event.id), response.json)

    def test_soft_delete_event(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(email=user.email))

        # when
        response = self.client.open(
            "/delete_events",
            query_string=self.hmac_query_params,
            method="PUT",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                fixtures.delete_event_request(event_id=event.id, user_id=user.id),
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 204)

    def test_get_events_with_attendees_by_user_email(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(email=user.email))
        look = self.look_service.create_look(fixtures.look_request(event_id=event.id, user_id=user.id))
        role = self.role_service.create_role(fixtures.role_request(event_id=event.id))
        self.attendee_service.create_attendee(
            fixtures.attendee_request(event_id=event.id, email=user.email, role=role.id, look_id=look.id)
        )

        # when
        response = self.client.open(
            "/events_attendees/{email}".format(email=user.email),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]["event_id"], str(event.id))
        self.assertEqual(response.json[0]["event_name"], event.event_name)
        self.assertEqual(response.json[0]["event_date"], str(event.event_date))
        self.assertEqual(response.json[0]["user_id"], str(event.user_id))
        self.assertEqual(response.json[0]["look_id"], str(look.id))
        self.assertEqual(response.json[0]["look_name"], look.look_name)
