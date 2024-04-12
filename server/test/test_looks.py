from __future__ import absolute_import

import json
import uuid

from server import encoder
from server.database.models import Look
from server.services.event import EventService
from server.services.look import LookService
from server.services.user import UserService
from server.test import BaseTestCase
from server.test.fixtures import create_look_request_payload, create_user_request_payload, create_event_request_payload


class TestLooks(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.look_service = LookService(self.session_factory)
        self.user_service = UserService(self.session_factory)
        self.event_service = EventService(self.session_factory)

    def assert_equal_response_look_with_db_look(self, look: Look, response_look: dict):
        self.assertEqual(response_look["id"], str(look.id))
        self.assertEqual(response_look["look_name"], look.look_name)
        self.assertEqual(response_look["event_id"], str(look.event_id))
        self.assertEqual(response_look["user_id"], str(look.user_id))
        self.assertEqual(response_look["product_specs"], look.product_specs)
        self.assertEqual(response_look["product_final_image"], look.product_final_image)

    def test_get_list_of_all_looks_from_empty_db(self):
        # when
        response = self.client.open(
            "/looks",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_list_of_all_looks(self):
        # given
        user1 = self.user_service.create_user(**create_user_request_payload())
        user2 = self.user_service.create_user(**create_user_request_payload())
        event1 = self.event_service.create_event(**create_event_request_payload(user_id=user1.id))
        event2 = self.event_service.create_event(**create_event_request_payload(user_id=user2.id))
        look11 = self.look_service.create_look(**create_look_request_payload(event_id=event1.id, user_id=user1.id))
        look21 = self.look_service.create_look(**create_look_request_payload(event_id=event2.id, user_id=user1.id))
        look22 = self.look_service.create_look(**create_look_request_payload(event_id=event2.id, user_id=user2.id))

        # when
        response = self.client.open(
            "/looks",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 3)
        self.assert_equal_response_look_with_db_look(look11, response.json[0])
        self.assert_equal_response_look_with_db_look(look21, response.json[1])
        self.assert_equal_response_look_with_db_look(look22, response.json[2])

    def test_get_empty_list_of_looks_user(self):
        query_params = {**self.hmac_query_params.copy(), "user_id": str(uuid.uuid4())}

        response = self.client.open(
            "/looks_with_userid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_list_of_looks_for_user_by_id(self):
        # given
        user1 = self.user_service.create_user(**create_user_request_payload())
        user2 = self.user_service.create_user(**create_user_request_payload())
        event1 = self.event_service.create_event(**create_event_request_payload(user_id=user1.id))
        event2 = self.event_service.create_event(**create_event_request_payload(user_id=user2.id))
        look11 = self.look_service.create_look(**create_look_request_payload(event_id=event1.id, user_id=user1.id))
        look21 = self.look_service.create_look(**create_look_request_payload(event_id=event2.id, user_id=user1.id))
        look22 = self.look_service.create_look(**create_look_request_payload(event_id=event2.id, user_id=user2.id))

        # when
        query_params = {**self.hmac_query_params.copy(), "user_id": str(user1.id)}

        response = self.client.open(
            "/looks_with_userid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assert_equal_response_look_with_db_look(look11, response.json[0])
        self.assert_equal_response_look_with_db_look(look21, response.json[1])

    def test_get_look_by_id_and_user(self):
        # given
        user = self.user_service.create_user(**create_user_request_payload())
        event = self.event_service.create_event(**create_event_request_payload(user_id=user.id))
        look = self.look_service.create_look(**create_look_request_payload(event_id=event.id, user_id=user.id))

        # when
        query_params = {**self.hmac_query_params.copy(), "look_id": str(look.id), "user_id": str(user.id)}

        response = self.client.open(
            "/looks_with_lookid_userid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assert_equal_response_look_with_db_look(look, response.json)

    def test_get_look_by_id_and_non_existing_user(self):
        # given
        user = self.user_service.create_user(**create_user_request_payload())
        event = self.event_service.create_event(**create_event_request_payload(user_id=user.id))
        look = self.look_service.create_look(**create_look_request_payload(event_id=event.id, user_id=user.id))

        # when
        query_params = {**self.hmac_query_params.copy(), "look_id": str(look.id), "user_id": str(uuid.uuid4())}

        response = self.client.open(
            "/looks_with_lookid_userid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_get_look_non_existing_look_id(self):
        # given
        user = self.user_service.create_user(**create_user_request_payload())

        # when
        query_params = {**self.hmac_query_params.copy(), "look_id": str(uuid.uuid4()), "user_id": str(user.id)}

        response = self.client.open(
            "/looks_with_lookid_userid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_create_look_without_user(self):
        # when
        look_request = create_look_request_payload()
        look_request["email"] = f"{str(uuid.uuid4())}@example.com"
        del look_request["user_id"]
        del look_request["event_id"]

        response = self.client.open(
            "/looks",
            query_string=self.hmac_query_params,
            data=json.dumps(look_request, cls=encoder.CustomJSONEncoder),
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_create_look_without_event(self):
        # when
        user = self.user_service.create_user(**create_user_request_payload())

        look_request = create_look_request_payload(user_id=str(user.id))
        enriched_look_request = {**look_request, "email": user.email}
        del enriched_look_request["user_id"]
        del enriched_look_request["event_id"]

        response = self.client.open(
            "/looks",
            query_string=self.hmac_query_params,
            data=json.dumps(enriched_look_request, cls=encoder.CustomJSONEncoder),
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNone(response.json["event_id"])
        self.assert_equal_left(look_request, response.json)

    def test_create_look_with_event(self):
        # when
        user = self.user_service.create_user(**create_user_request_payload())
        event = self.event_service.create_event(**create_event_request_payload(user_id=user.id))

        look_request = create_look_request_payload(user_id=str(user.id), event_id=str(event.id))
        enriched_look_request = {**look_request, "email": user.email}
        del enriched_look_request["user_id"]

        response = self.client.open(
            "/looks",
            query_string=self.hmac_query_params,
            data=json.dumps(enriched_look_request, cls=encoder.CustomJSONEncoder),
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["event_id"])
        self.assert_equal_left(look_request, response.json)

    def test_get_look_by_id_and_event_id(self):
        # given
        user = self.user_service.create_user(**create_user_request_payload())
        event = self.event_service.create_event(**create_event_request_payload(user_id=user.id))
        look = self.look_service.create_look(**create_look_request_payload(event_id=event.id, user_id=user.id))

        # when
        query_params = {**self.hmac_query_params.copy(), "look_id": str(look.id), "user_id": str(uuid.uuid4())}

        response = self.client.open(
            "/looks_with_lookid_userid",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_update_look(self):
        # intentionally failing here, work in progress
        self.assertStatus(None, 404)
