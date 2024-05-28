from __future__ import absolute_import

import json
import uuid

from server import encoder
from server.database.models import Look
from server.test import BaseTestCase, fixtures


class TestLooks(BaseTestCase):
    def test_create_look(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        look_data = fixtures.create_look_request(user_id=user.id, product_specs={"variants": [123, 234, 345]})

        response = self.client.open(
            "/looks",
            query_string=self.hmac_query_params,
            data=look_data.json(),
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])
        self.assertEqual(response.json["name"], look_data.name)
        db_look = self.look_service.get_look_by_id(response.json["id"])
        self.assertIsNotNone(db_look)
        self.assertEqual(db_look.product_specs, look_data.product_specs)
        self.assertEqual(db_look.user_id, user.id)

    def test_create_look_duplicate(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        look = self.look_service.create_look(fixtures.create_look_request(user_id=user.id))

        # when
        look_data = fixtures.create_look_request(user_id=user.id, name=look.name)

        response = self.client.open(
            "/looks",
            query_string=self.hmac_query_params,
            data=look_data.json(),
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
        self.assert404(response)

    def test_look_by_id(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        look = self.look_service.create_look(fixtures.create_look_request(user_id=user.id))

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
        self.assertIsNotNone(response.json["id"])
        self.assertEqual(response.json["name"], look.name)

    def test_update_look_for_invalid_look_id(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        update_look_request = fixtures.update_look_request(user_id=user.id)

        response = self.client.open(
            f"/looks/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            data=update_look_request.json(),
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_update_look(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs={"variants": [123, 234, 345]})
        )
        role = self.role_service.create_role(fixtures.create_role_request(event_id=str(event.id)))
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=user.email, event_id=str(event.id), role_id=role.id, look_id=look.id)
        )

        # when
        update_look_request = fixtures.update_look_request(
            name=f"{str(uuid.uuid4())}-new_name",
            product_specs={"variants": [987, 876]},
        )

        response = self.client.open(
            f"/looks/{str(look.id)}",
            query_string=self.hmac_query_params,
            data=update_look_request.json(),
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json["id"], str(look.id))
        self.assertEqual(response.json["name"], str(update_look_request.name))
        self.assertEqual(update_look_request.product_specs, update_look_request.product_specs)

        updated_db_look = Look.query.filter(Look.id == look.id).first()
        self.assertEqual(updated_db_look.user_id, user.id)
        self.assertEqual(updated_db_look.name, update_look_request.name)
        self.assertEqual(updated_db_look.product_specs, update_look_request.product_specs)

    def test_update_look_existing(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(fixtures.create_look_request(user_id=str(user.id)))
        look2 = self.look_service.create_look(fixtures.create_look_request(user_id=str(user.id)))
        role = self.role_service.create_role(fixtures.create_role_request(event_id=str(event.id)))
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=user.email, event_id=event.id, role_id=role.id, look_id=look.id)
        )

        # when
        update_look_request = fixtures.update_look_request(
            user_id=str(user.id),
            name=look2.name,
        )

        response = self.client.open(
            f"/looks/{str(look.id)}",
            query_string=self.hmac_query_params,
            data=update_look_request.json(),
            method="PUT",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 409)

    def test_get_looks_for_non_existed_event(self):
        # when
        response = self.client.open(
            f"/looks/{str(uuid.uuid4())}/events",
            query_string=self.hmac_query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_get_events_for_look(self):
        user1 = self.user_service.create_user(fixtures.create_user_request())
        user2 = self.user_service.create_user(fixtures.create_user_request())
        event1 = self.event_service.create_event(fixtures.create_event_request(user_id=user1.id))
        event2 = self.event_service.create_event(fixtures.create_event_request(user_id=user2.id))
        look = self.look_service.create_look(fixtures.create_look_request(user_id=user1.id))
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event1.id, email=user1.email, look_id=look.id)
        )
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event2.id, email=user2.email, look_id=look.id)
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
        self.assertEqual(response.json[0]["name"], event1.name)
        self.assertEqual(response.json[1]["id"], str(event2.id))
        self.assertEqual(response.json[1]["name"], event2.name)

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
        self.assert404(response)

    def test_delete_look(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        look = self.look_service.create_look(fixtures.create_look_request(user_id=user.id))

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
        look_in_db = Look.query.filter(Look.id == look.id).first()
        self.assertIsNone(look_in_db)

    def test_create_look_with_name_too_long(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        look_data = fixtures.create_look_request(
            user_id=user.id, product_specs={"variants": [123, 234, 345]}
        ).model_dump()
        look_data["name"] = "a" * 256

        response = self.client.open(
            "/looks",
            query_string=self.hmac_query_params,
            data=json.dumps(look_data, cls=encoder.CustomJSONEncoder),
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 400)
        self.assertEqual(response.json["errors"], "Look name must be between 2 and 64 characters long")
