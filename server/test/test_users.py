from __future__ import absolute_import

import json
import uuid

from server import encoder
from server.database.models import User
from server.services.attendee import AttendeeService
from server.services.event import EventService
from server.services.user import UserService
from server.test import BaseTestCase, fixtures


class TestUsers(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.user_service = UserService()
        self.event_service = EventService()
        self.attendee_service = AttendeeService()

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

    def test_get_existing_user_by_email(self):
        # given
        email = f"{str(uuid.uuid4())}@example.com"
        user = self.user_service.create_user(fixtures.user_request(email=email))

        # when
        response = self.client.open(
            "/users/{email}".format(email=email), query_string=self.hmac_query_params, method="GET"
        )

        # then
        self.assert200(response)
        self.assert_equal_response_user_with_db_user(user, response.json)

    def test_create_user(self):
        # when
        user = fixtures.user_request()

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
        user = fixtures.user_request()
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

    def test_update_non_existing_user(self):
        # when
        user = fixtures.user_request()

        response = self.client.open(
            f"/users/{str(uuid.uuid4())}",
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
        user = self.user_service.create_user(fixtures.user_request())

        # when
        updated_user = fixtures.update_user_request(
            account_status=not user.account_status,
        )
        updated_user["email"] = str(uuid.uuid4()) + "@example.com"

        response = self.client.open(
            f"/users/{str(user.id)}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(updated_user, cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(str(user.id), response.json["id"])
        self.assertEqual(user.email, response.json["email"])
        self.assertEqual(updated_user.get("first_name"), response.json["first_name"])
        self.assertEqual(updated_user.get("last_name"), response.json["last_name"])
        self.assertEqual(updated_user.get("account_status"), response.json["account_status"])
        self.assertEqual(updated_user.get("shopify_id"), response.json["shopify_id"])

    def test_get_all_events_for_non_existing_user(self):
        # when
        response = self.client.open(
            f"/users/{str(uuid.uuid4())}/events",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json, [])

    def test_get_all_events_for_user_without_events(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())

        # when
        response = self.client.open(
            f"/users/{user.id}/events",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json, [])

    def test_get_all_active_events_for_user(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event1 = self.event_service.create_event(fixtures.event_request(email=user.email))
        event2 = self.event_service.create_event(fixtures.event_request(email=user.email))
        self.event_service.create_event(fixtures.event_request(email=user.email, is_active=False))

        # when
        response = self.client.open(
            f"/users/{user.id}/events",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 2)
        self.assertEqual(response.json[0]["id"], str(event1.id))
        self.assertEqual(response.json[0]["event_name"], str(event1.event_name))
        self.assertEqual(response.json[1]["id"], str(event2.id))
        self.assertEqual(response.json[1]["event_name"], str(event2.event_name))

    def test_get_invites_for_non_existing_user(self):
        # when
        response = self.client.open(
            f"/users/{str(uuid.uuid4())}/invites",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 0)

    def test_get_invites_for_existing_user_but_without_events(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())

        # when
        response = self.client.open(
            f"/users/{str(user.id)}/invites",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 0)

    def test_get_invites_for_one_event(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        attendee_user = self.user_service.create_user(fixtures.user_request())
        event1 = self.event_service.create_event(fixtures.event_request(email=user.email))
        self.attendee_service.create_attendee(fixtures.attendee_request(event_id=event1.id, email=attendee_user.email))
        self.event_service.create_event(fixtures.event_request(email=attendee_user.email))

        # when
        response = self.client.open(
            f"/users/{str(attendee_user.id)}/invites",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 1)
        response_event = response.json[0]
        self.assertEqual(response_event["id"], str(event1.id))

    def test_get_invites_for_multiple_events(self):
        # given
        attendee_user = self.user_service.create_user(fixtures.user_request())
        user1 = self.user_service.create_user(fixtures.user_request())
        user2 = self.user_service.create_user(fixtures.user_request())
        event1 = self.event_service.create_event(fixtures.event_request(email=user1.email))
        event2 = self.event_service.create_event(fixtures.event_request(email=user2.email))
        event3 = self.event_service.create_event(fixtures.event_request(email=user1.email, is_active=False))
        self.attendee_service.create_attendee(fixtures.attendee_request(event_id=event1.id, email=attendee_user.email))
        self.attendee_service.create_attendee(fixtures.attendee_request(event_id=event2.id, email=attendee_user.email))
        self.attendee_service.create_attendee(fixtures.attendee_request(event_id=event3.id, email=attendee_user.email))

        # when
        response = self.client.open(
            f"/users/{str(attendee_user.id)}/invites",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 2)
        response_event1 = response.json[0]
        response_event2 = response.json[1]
        self.assertEqual(response_event1["id"], str(event1.id))
        self.assertEqual(response_event2["id"], str(event2.id))
