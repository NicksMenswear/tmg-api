from __future__ import absolute_import

import json
import uuid
from datetime import datetime, timedelta

from server import encoder
from server.test import BaseTestCase, fixtures


class TestEvents(BaseTestCase):
    def test_create_event_for_non_existing_user(self):
        # when
        response = self.client.open(
            "/events",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=fixtures.create_event_request().json(),
        )

        # then
        self.assert404(response)

    def test_create_event_duplicate(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        response = self.client.open(
            "/events",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=fixtures.create_event_request(name=event.name, user_id=user.id, is_active=True).json(),
        )

        # then
        self.assertStatus(response, 409)

    def test_create_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        event_request = fixtures.create_event_request(user_id=user.id)

        response = self.client.open(
            "/events",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=event_request.json(),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json.get("id"))
        self.assertEqual(response.json.get("name"), event_request.name)
        self.assertEqual(response.json.get("event_at"), str(event_request.event_at.isoformat()))
        self.assertEqual(response.json.get("user_id"), str(event_request.user_id))

    def test_get_event_non_existing(self):
        # when
        response = self.client.open(
            f"/events/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert404(response)

    def test_get_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event_request = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        response = self.client.open(
            f"/events/{event_request.id}",
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert200(response)
        self.assertIsNotNone(response.json.get("id"))
        self.assertEqual(response.json.get("name"), event_request.name)
        self.assertEqual(response.json.get("event_at"), str(event_request.event_at.isoformat()))
        self.assertEqual(response.json.get("user_id"), str(event_request.user_id))

    def test_get_event_non_active(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id, is_active=False))

        # when
        response = self.client.open(
            f"/events/{event.id}",
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert200(response)
        self.assertIsNotNone(response.json.get("id"))

    # def test_get_event_enriched_without_attendees(self):
    #     # given
    #     user = self.user_service.create_user(fixtures.create_user_request())
    #     event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
    #
    #     # when
    #     query_params = {**self.hmac_query_params.copy(), "enriched": "true"}
    #     response = self.client.open(
    #         f"/events/{event.id}",
    #         query_string=query_params,
    #         method="GET",
    #         content_type=self.content_type,
    #         headers=self.request_headers,
    #     )
    #
    #     # then
    #     self.assert200(response)
    #     response_event = response.json
    #     self.assert_equal_response_event_with_db_event(
    #         self.event_service.get_event_by_id(response.json["id"]).to_dict(), response_event
    #     )
    #     self.assertEqual(response_event["attendees"], [])
    #
    # def test_get_event_enriched_with_2_out_of_3_attendees_active(self):
    #     # given
    #     user = self.user_service.create_user(fixtures.create_user_request())
    #     event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
    #     attendee_user1 = self.user_service.create_user(fixtures.create_user_request())
    #     attendee_user2 = self.user_service.create_user(fixtures.create_user_request())
    #     attendee_user3 = self.user_service.create_user(fixtures.create_user_request())
    #     attendee1 = self.attendee_service.create_attendee(
    #         fixtures.attendee_request(email=attendee_user1.email, event_id=event.id)
    #     )
    #     attendee2 = self.attendee_service.create_attendee(
    #         fixtures.attendee_request(email=attendee_user2.email, event_id=event.id)
    #     )
    #     self.attendee_service.create_attendee(
    #         fixtures.attendee_request(email=attendee_user3.email, event_id=event.id, is_active=False)
    #     )
    #
    #     # when
    #     query_params = {**self.hmac_query_params.copy(), "enriched": "true"}
    #     response = self.client.open(
    #         f"/events/{event.id}",
    #         query_string=query_params,
    #         method="GET",
    #         content_type=self.content_type,
    #         headers=self.request_headers,
    #     )
    #
    #     # then
    #     self.assert200(response)
    #     response_event = response.json
    #     self.assert_equal_response_event_with_db_event(
    #         self.event_service.get_event_by_id(response.json["id"]).to_dict(), response_event
    #     )
    #     self.assertEqual(len(response_event["attendees"]), 2)
    #     response_attendee1 = response_event["attendees"][0]
    #     response_attendee2 = response_event["attendees"][1]
    #     self.assertNotEqual(str(attendee1.id), str(attendee2.id))
    #     self.assertTrue(str(attendee1.id) in [response_attendee1["id"], response_attendee2["id"]])
    #     self.assertTrue(str(attendee2.id) in [response_attendee1["id"], response_attendee2["id"]])
    #
    # def test_get_event_enriched_attendee_look_and_role(self):
    #     # given
    #     user = self.user_service.create_user(fixtures.create_user_request())
    #     event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
    #     attendee_user = self.user_service.create_user(fixtures.create_user_request())
    #     look = self.look_service.create_look(fixtures.create_look_request(user_id=user.id))
    #     role = self.role_service.create_role(fixtures.role_request(event_id=event.id))
    #     attendee = self.attendee_service.create_attendee(
    #         fixtures.attendee_request(email=attendee_user.email, event_id=event.id, look_id=look.id, role_id=role.id)
    #     )
    #
    #     # when
    #     query_params = {**self.hmac_query_params.copy(), "enriched": "true"}
    #     response = self.client.open(
    #         f"/events/{event.id}",
    #         query_string=query_params,
    #         method="GET",
    #         content_type=self.content_type,
    #         headers=self.request_headers,
    #     )
    #
    #     # then
    #     self.assert200(response)
    #
    #     response_event = response.json
    #     self.assertEqual(response_event["user_id"], str(user.id))
    #
    #     self.assertEqual(len(response_event["attendees"]), 1)
    #     response_attendee = response_event["attendees"][0]
    #     self.assertEqual(response_attendee["id"], str(attendee.id))
    #     self.assertEqual(response_attendee["invite"], attendee.invite)
    #     self.assertEqual(response_attendee["pay"], attendee.pay)
    #     self.assertEqual(response_attendee["ship"], attendee.ship)
    #     self.assertEqual(response_attendee["size"], attendee.size)
    #     self.assertEqual(response_attendee["style"], attendee.style)
    #
    #     response_attendee_look = response_attendee["look"]
    #     self.assertEqual(response_attendee_look["id"], str(look.id))
    #     self.assertEqual(response_attendee_look["name"], look.name)
    #     self.assertEqual(response_attendee_look["product_specs"], look.product_specs)
    #
    #     response_attendee_role = response_attendee["role_id"]
    #     self.assertEqual(response_attendee_role["id"], str(role.id))
    #     self.assertEqual(response_attendee_role["name"], role.name)
    #
    #     response_attendee_user = response_attendee["user"]
    #     self.assertEqual(response_attendee_user["id"], str(attendee_user.id))
    #     self.assertEqual(response_attendee_user["email"], attendee_user.email)
    #     self.assertEqual(response_attendee_user["first_name"], attendee_user.first_name)
    #     self.assertEqual(response_attendee_user["last_name"], attendee_user.last_name)

    def test_get_roles_by_event_id(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        role1 = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        role2 = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))

        # when
        response = self.client.open(
            f"/events/{event.id}/roles",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        response_role1 = response.json[0]
        response_role2 = response.json[1]
        self.assertEqual(response_role1.get("id"), str(role1.id))
        self.assertEqual(response_role1.get("name"), role1.name)
        self.assertEqual(response_role2.get("id"), str(role2.id))
        self.assertEqual(response_role2.get("name"), role2.name)

    def test_get_roles_by_non_existing_event_id(self):
        # when
        response = self.client.open(
            f"/events/{str(uuid.uuid4())}/roles",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_get_roles_for_event_without_roles(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        response = self.client.open(
            f"/events/{str(event.id)}/roles",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_get_attendees_for_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(fixtures.create_look_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        attendee_user1 = self.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.user_service.create_user(fixtures.create_user_request())
        attendee_request1 = fixtures.create_attendee_request(
            event_id=event.id, email=attendee_user1.email, role_id=str(role.id)
        )
        attendee_request2 = fixtures.create_attendee_request(
            event_id=event.id, email=attendee_user2.email, role_id=str(role.id)
        )
        attendee1 = self.attendee_service.create_attendee(attendee_request1)
        attendee2 = self.attendee_service.create_attendee(attendee_request2)

        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id, email=attendee_user3.email, role_id=str(role.id), look_id=look.id, is_active=False
            )
        )

        # when
        response = self.client.open(
            f"/events/{str(event.id)}/attendees",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        response_attendee1 = response.json[0]
        response_attendee2 = response.json[1]
        self.assertNotEqual(str(attendee1.id), str(attendee2.id))
        self.assertTrue(str(attendee1.id) in [response_attendee1["id"], response_attendee2["id"]])
        self.assertTrue(str(attendee2.id) in [response_attendee1["id"], response_attendee2["id"]])

    def test_get_all_attendees_for_non_existing_event(self):
        # when
        response = self.client.open(
            f"/events/{str(uuid.uuid4())}/attendees",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_update_event_non_existed(self):
        # when
        response = self.client.open(
            f"/events/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="PUT",
            content_type=self.content_type,
            headers=self.request_headers,
            data=fixtures.update_event_request(
                name=str(uuid.uuid4()), event_at=(datetime.now() + timedelta(days=1)).isoformat()
            ).json(),
        )

        # then
        self.assert404(response)

    def test_update_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        updated_name = str(uuid.uuid4())
        updated_event_at = (datetime.now() + timedelta(days=1)).isoformat()

        response = self.client.open(
            f"/events/{str(event.id)}",
            query_string=self.hmac_query_params,
            method="PUT",
            content_type=self.content_type,
            headers=self.request_headers,
            data=fixtures.update_event_request(name=updated_name, event_at=updated_event_at).json(),
        )

        # then
        self.assert200(response)
        response_event = response.json
        self.assertEqual(response_event["name"], updated_name)
        self.assertEqual(response_event["event_at"], updated_event_at)

    def test_update_event_existing(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        event2 = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        response = self.client.open(
            f"/events/{str(event.id)}",
            query_string=self.hmac_query_params,
            method="PUT",
            content_type=self.content_type,
            headers=self.request_headers,
            data=fixtures.update_event_request(name=event2.name, event_at=event2.event_at).json(),
        )

        # then
        self.assertStatus(response, 409)

    def test_delete_event_non_existing(self):
        # when
        response = self.client.open(
            f"/events/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="DELETE",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assertStatus(response, 404)

    def test_delete_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        response = self.client.open(
            f"/events/{event.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assertStatus(response, 204)

        looked_up_event = self.event_service.get_event_by_id(event.id)
        self.assertEqual(looked_up_event.is_active, False)

    def test_create_event_name_too_short(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        event_request = fixtures.create_event_request(user_id=user.id).model_dump()
        event_request["name"] = "a"

        response = self.client.open(
            "/events",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(event_request, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 400)
        self.assertEqual(response.json["errors"], "Event name must be between 2 and 64 characters long")

    def test_create_event_at_in_the_past(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        event_request = fixtures.create_event_request(user_id=user.id).model_dump()
        event_request["event_at"] = (datetime.now() - timedelta(days=1)).isoformat()

        response = self.client.open(
            "/events",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(event_request, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 400)
        self.assertEqual(response.json["errors"], "Event date must be in the future")
