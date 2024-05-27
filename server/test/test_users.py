from __future__ import absolute_import

import json
import uuid

from server import encoder
from server.models.user_model import CreateUserModel, UserModel
from server.test import BaseTestCase, fixtures, utils


class TestUsers(BaseTestCase):
    def assert_equal_response_user_with_user_model(self, user: UserModel, response_user: dict):
        self.assertEqual(response_user["id"], str(user.id))
        self.assertEqual(response_user["first_name"], user.first_name)
        self.assertEqual(response_user["last_name"], user.last_name)
        self.assertEqual(response_user["email"], user.email)

    def test_get_non_existing_user_by_email(self):
        # when
        response = self.client.open(
            f"/users/{str(uuid.uuid4())}@example.com",
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_get_existing_user_by_email(self):
        # given
        email = f"{str(uuid.uuid4())}@example.com"
        user: UserModel = self.user_service.create_user(fixtures.create_user_request(email=email))

        # when
        response = self.client.open(f"/users/{email}", query_string=self.hmac_query_params, method="GET")

        # then
        self.assert200(response)
        self.assert_equal_response_user_with_user_model(user, response.json)

    def test_create_user(self):
        # when
        create_user: CreateUserModel = fixtures.create_user_request()

        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=create_user.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(create_user.first_name, response.json["first_name"])
        self.assertEqual(create_user.last_name, response.json["last_name"])
        self.assertEqual(create_user.email, response.json["email"])
        self.assertIsNotNone(response.json["id"])

    def test_update_non_existing_user(self):
        # when
        response = self.client.open(
            f"/users/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=fixtures.create_user_request().json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_update_user(self):
        # given
        user: UserModel = self.user_service.create_user(fixtures.create_user_request())

        # when
        updated_first_name = utils.generate_unique_name()
        updated_last_name = utils.generate_unique_name()

        updated_user = fixtures.update_user_request(first_name=updated_first_name, last_name=updated_last_name)

        response = self.client.open(
            f"/users/{str(user.id)}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=updated_user.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(str(user.id), response.json["id"])
        self.assertEqual(user.email, response.json["email"])
        self.assertEqual(updated_user.first_name, response.json["first_name"])
        self.assertEqual(updated_user.last_name, response.json["last_name"])

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
        self.assert404(response)

    def test_get_all_events_for_user_without_events(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

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
        user = self.user_service.create_user(fixtures.create_user_request())
        event1 = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        event2 = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        self.event_service.create_event(fixtures.create_event_request(user_id=user.id, is_active=False))

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
            f"/users/{str(uuid.uuid4())}/events",
            query_string={**self.hmac_query_params, "status": "attendee"},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_get_invites_for_existing_user_but_without_events(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        response = self.client.open(
            f"/users/{str(user.id)}/events",
            query_string={**self.hmac_query_params, "status": "attendee"},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 0)

    def test_get_invites_for_one_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        event1 = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event1.id, email=attendee_user.email)
        )
        self.event_service.create_event(fixtures.create_event_request(user_id=attendee_user.id))

        # when
        response = self.client.open(
            f"/users/{str(attendee_user.id)}/events",
            query_string={**self.hmac_query_params, "status": "attendee"},
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
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        user1 = self.user_service.create_user(fixtures.create_user_request())
        user2 = self.user_service.create_user(fixtures.create_user_request())
        event1 = self.event_service.create_event(fixtures.create_event_request(user_id=user1.id))
        event2 = self.event_service.create_event(fixtures.create_event_request(user_id=user2.id))
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event1.id, email=attendee_user.email)
        )
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event2.id, email=attendee_user.email)
        )

        # when
        response = self.client.open(
            f"/users/{str(attendee_user.id)}/events",
            query_string={**self.hmac_query_params, "status": "attendee"},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 2)
        self.assertEqual({response.json[0]["id"], response.json[1]["id"]}, {str(event1.id), str(event2.id)})

    def test_get_events_of_mix_statuses(self):
        # given
        user1 = self.user_service.create_user(fixtures.create_user_request())
        event1 = self.event_service.create_event(fixtures.create_event_request(user_id=user1.id))
        user2 = self.user_service.create_user(fixtures.create_user_request())
        event2 = self.event_service.create_event(fixtures.create_event_request(user_id=user2.id))
        event3_owner_inactive = self.event_service.create_event(
            fixtures.create_event_request(user_id=user2.id, is_active=False)
        )
        event4_invited_inactive = self.event_service.create_event(
            fixtures.create_event_request(user_id=user1.id, is_active=False)
        )
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event1.id, email=user2.email))

        # when
        response = self.client.open(
            f"/users/{str(user2.id)}/events",
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
        self.assertTrue(response_event1["id"] in (str(event1.id), str(event2.id)))
        self.assertTrue(response_event2["id"] in (str(event1.id), str(event2.id)))

    def test_get_user_looks_for_non_existing_user(self):
        # when
        response = self.client.open(
            f"/users/{str(uuid.uuid4())}/looks",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_user_looks_empty_list(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        response = self.client.open(
            f"/users/{str(user.id)}/looks",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_list_of_looks_for_user_by_id(self):
        # given
        user1 = self.user_service.create_user(fixtures.create_user_request())
        user2 = self.user_service.create_user(fixtures.create_user_request())
        look1 = self.look_service.create_look(fixtures.create_look_request(user_id=user1.id))
        look2 = self.look_service.create_look(fixtures.create_look_request(user_id=user1.id))
        self.look_service.create_look(fixtures.create_look_request(user_id=user2.id))

        # when
        response = self.client.open(
            f"/users/{str(user1.id)}/looks",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)

        response_look1 = response.json[0]
        response_look2 = response.json[1]

        self.assertEqual(response_look1["id"], str(look1.id))
        self.assertEqual(response_look1["look_name"], str(look1.look_name))
        self.assertEqual(response_look2["id"], str(look2.id))
        self.assertEqual(response_look2["look_name"], str(look2.look_name))

    def test_create_user_first_name_too_short(self):
        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(
                {"first_name": "a", "last_name": "abcd", "email": "test@example.com"},
                cls=encoder.CustomJSONEncoder,
            ),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 400)

    def test_create_user_last_name_too_long(self):
        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(
                {
                    "first_name": "abcdefghij",
                    "last_name": "abcdefghijabcdefghijabcdefghijabcdefghijabcdefghijabcdefghijabcdefghijabcdefghijabcdefghijabcdefghij",
                    "email": "test@example.com",
                },
                cls=encoder.CustomJSONEncoder,
            ),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 400)

    def test_create_user_first_name_invalid_characters(self):
        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(
                {
                    "first_name": "123",
                    "last_name": "abcdefg",
                    "email": "test@example.com",
                },
                cls=encoder.CustomJSONEncoder,
            ),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 400)

    def test_create_user_invalid_email(self):
        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(
                {
                    "first_name": "abcdefg",
                    "last_name": "abcdefg",
                    "email": "not-an-email",
                },
                cls=encoder.CustomJSONEncoder,
            ),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 400)
