from __future__ import absolute_import

import json
import uuid

from server import encoder
from server.tests.integration import BaseTestCase, fixtures


class TestRoles(BaseTestCase):
    def test_create_role(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        create_role = fixtures.create_role_request(event_id=event.id)

        response = self.client.open(
            "/roles",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=create_role.json(),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])
        self.assertEqual(response.json["name"], create_role.name)
        self.assertEqual(response.json["event_id"], str(create_role.event_id))

    def test_create_role_event_not_found(self):
        # when
        create_role = fixtures.create_role_request(event_id=str(uuid.uuid4()))

        response = self.client.open(
            "/roles",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=create_role.json(),
        )

        # then
        self.assertStatus(response, 404)

    def test_create_role_with_same_name_as_existing(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))

        # when
        create_role = fixtures.create_role_request(event_id=event.id, name=role.name)

        response = self.client.open(
            "/roles",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=create_role.json(),
        )

        # then
        self.assertStatus(response, 409)

    def test_create_role_with_same_name_as_existing_but_not_active(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id, is_active=False))

        # when
        create_role = fixtures.create_role_request(event_id=event.id, name=role.name)

        response = self.client.open(
            "/roles",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=create_role.json(),
        )

        # then
        self.assertStatus(response, 201)

    def test_get_role_by_id(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))

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
        self.assertIsNotNone(response.json["id"])
        self.assertEqual(response.json["name"], role.name)
        self.assertEqual(response.json["event_id"], str(role.event_id))

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

    def test_update_role(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))

        # when
        new_name = role.name + "-updated"
        update_role = fixtures.update_role_request(name=new_name)

        response = self.client.open(
            f"/roles/{str(role.id)}",
            query_string=self.hmac_query_params,
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
            data=update_role.json(),
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json["id"], str(role.id))
        self.assertEqual(response.json["name"], new_name)
        self.assertEqual(response.json["event_id"], str(event.id))

    def test_update_role_invalid_id(self):
        # when
        response = self.client.open(
            f"/roles/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
            data=fixtures.update_role_request(name="test").json(),
        )

        # then
        self.assertStatus(response, 404)

    def test_update_role_with_existing_name(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        role1 = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        role2 = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))

        # when
        response = self.client.open(
            f"/roles/{str(role1.id)}",
            query_string=self.hmac_query_params,
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
            data=fixtures.update_role_request(name=role2.name).json(),
        )

        # then
        self.assertStatus(response, 409)

    def test_delete_role_non_existing(self):
        # when
        response = self.client.open(
            f"/roles/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="DELETE",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_delete_role(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))

        # when
        response = self.client.open(
            f"/roles/{role.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 204)
        role_in_db = self.role_service.get_role_by_id(role.id)
        self.assertEqual(role_in_db.is_active, False)

    def test_delete_role_associated_to_attendee(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, role_id=role.id))

        # when
        response = self.client.open(
            f"/roles/{role.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 400)
        self.assertEqual(response.json["errors"], "Can't delete role associated to attendee")

    def test_create_role_with_name_too_short(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        create_role = fixtures.create_role_request(event_id=event.id).model_dump()
        create_role["name"] = "a"

        response = self.client.open(
            "/roles",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(create_role, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 400)
        self.assertEqual(response.json["errors"], "Role name must be between 2 and 64 characters long")
