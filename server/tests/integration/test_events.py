from __future__ import absolute_import

import json
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from server import encoder
from server.controllers import FORCE_DELETE_HEADER
from server.database.database_manager import db
from server.database.models import Attendee
from server.models.event_model import EventTypeModel
from server.services.event_service import NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION
from server.services.role_service import PREDEFINED_ROLES
from server.tests.integration import BaseTestCase, fixtures


class TestEvents(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.populate_shopify_variants()

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
            data=fixtures.create_event_request(
                name=event.name, event_at=event.event_at, user_id=user.id, is_active=True
            ).json(),
        )

        # then
        self.assertStatus(response, 409)

    def test_create_wedding_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        event_request = fixtures.create_event_request(user_id=user.id, type=EventTypeModel.WEDDING)

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

        created_event = response.json
        self.assertIsNotNone(created_event.get("id"))
        self.assertEqual(created_event.get("name"), event_request.name)
        self.assertEqual(created_event.get("event_at"), str(event_request.event_at.isoformat()))
        event_owner = created_event.get("owner")
        self.assertIsNotNone(event_owner)
        self.assertEqual(event_owner.get("id"), str(event_request.user_id))
        self.assertEqual(event_owner.get("email"), user.email)
        self.assertEqual(event_owner.get("first_name"), user.first_name)
        self.assertEqual(event_owner.get("last_name"), user.last_name)
        self.assertEqual(created_event.get("type"), str(EventTypeModel.WEDDING))

        roles = self.role_service.get_roles_for_event(uuid.UUID(created_event.get("id")))
        unique_roles = set([role.name for role in roles])
        self.assertEqual(unique_roles, set(PREDEFINED_ROLES[EventTypeModel.WEDDING]))

    def test_create_prom_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        event_request = fixtures.create_event_request(user_id=user.id, type=EventTypeModel.PROM)

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

        created_event = response.json
        self.assertIsNotNone(created_event.get("id"))
        self.assertEqual(created_event.get("name"), event_request.name)
        self.assertEqual(created_event.get("event_at"), str(event_request.event_at.isoformat()))
        event_owner = created_event.get("owner")
        self.assertIsNotNone(event_owner)
        self.assertEqual(event_owner.get("id"), str(event_request.user_id))
        self.assertEqual(event_owner.get("email"), user.email)
        self.assertEqual(event_owner.get("first_name"), user.first_name)
        self.assertEqual(event_owner.get("last_name"), user.last_name)
        self.assertEqual(created_event.get("type"), str(EventTypeModel.PROM))

        roles = self.role_service.get_roles_for_event(uuid.UUID(created_event.get("id")))
        unique_roles = set([role.name for role in roles])
        self.assertEqual(unique_roles, set(PREDEFINED_ROLES[EventTypeModel.PROM]))

    def test_create_event_of_type_other(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        event_request = fixtures.create_event_request(user_id=user.id, type=EventTypeModel.OTHER)

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

        created_event = response.json
        self.assertIsNotNone(created_event.get("id"))
        self.assertEqual(created_event.get("name"), event_request.name)
        self.assertEqual(created_event.get("event_at"), str(event_request.event_at.isoformat()))
        event_owner = created_event.get("owner")
        self.assertIsNotNone(event_owner)
        self.assertEqual(event_owner.get("id"), str(event_request.user_id))
        self.assertEqual(event_owner.get("email"), user.email)
        self.assertEqual(event_owner.get("first_name"), user.first_name)
        self.assertEqual(event_owner.get("last_name"), user.last_name)
        self.assertEqual(created_event.get("type"), str(EventTypeModel.OTHER))
        roles = self.role_service.get_roles_for_event(uuid.UUID(created_event.get("id")))
        unique_roles = set([role.name for role in roles])
        self.assertEqual(unique_roles, set(PREDEFINED_ROLES[EventTypeModel.OTHER]))

    def test_create_event_without_type(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        event_request = fixtures.create_event_request(user_id=user.id)

        data = event_request.model_dump()
        del data["type"]

        response = self.client.open(
            "/events",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(data, cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assertStatus(response, 201)

        created_event = response.json
        self.assertIsNotNone(created_event.get("id"))
        self.assertEqual(created_event.get("name"), event_request.name)
        self.assertEqual(created_event.get("event_at"), str(event_request.event_at.isoformat()))
        self.assertIsNotNone(created_event.get("owner"))
        self.assertEqual(created_event.get("type"), str(EventTypeModel.WEDDING))

    def test_create_too_early_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        event_request = fixtures.create_event_request(
            user_id=user.id,
            type=EventTypeModel.WEDDING,
            event_at=datetime.now()
            + timedelta(weeks=NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION)
            - timedelta(days=2),
        )

        response = self.client.open(
            "/events",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=event_request.json(),
        )

        # then
        self.assertStatus(response, 400)
        self.assertEqual(
            response.json["errors"],
            f"You can only create events up to {NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION} weeks in advance. Please choose a date that is within the next {NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION} weeks.",
        )

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
        event_owner = response.json.get("owner")
        self.assertIsNotNone(event_owner)
        self.assertEqual(event_owner.get("id"), str(event_request.user_id))
        self.assertEqual(event_owner.get("email"), user.email)
        self.assertEqual(event_owner.get("first_name"), user.first_name)
        self.assertEqual(event_owner.get("last_name"), user.last_name)

    def test_get_event_enriched_without_attendees_looks(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event_request = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        response = self.client.open(
            f"/events/{event_request.id}",
            query_string={**self.hmac_query_params.copy(), "enriched": True},
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert200(response)
        self.assertIsNotNone(response.json.get("id"))
        self.assertEqual(response.json.get("name"), event_request.name)
        self.assertEqual(response.json.get("event_at"), str(event_request.event_at.isoformat()))
        self.assertIsNotNone(response.json.get("owner"))
        self.assertEqual(response.json.get("attendees"), [])
        self.assertEqual(response.json.get("looks"), [])

    def test_get_event_enriched_with_one_active_attendee_but_with_one_active_look_and_one_active_role(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        look2 = self.look_service.create_look(
            fixtures.create_look_request(
                user_id=user.id, is_active=False, product_specs=self.create_look_test_product_specs()
            )
        )
        role1 = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        role2 = self.role_service.create_role(fixtures.create_role_request(event_id=event.id, is_active=False))
        attendee_user1 = self.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id, email=attendee_user1.email, look_id=look1.id, role_id=role1.id
            )
        )
        order = self.order_service.create_order(
            fixtures.create_order_request(
                user_id=attendee_user1.id, event_id=event.id, outbound_tracking="123123", shopify_order_id="777"
            )
        )
        attendee_user2 = self.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user2.email, is_active=False)
        )

        # when
        response = self.client.open(
            f"/events/{event.id}",
            query_string={**self.hmac_query_params.copy(), "enriched": True},
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert200(response)
        self.assertIsNotNone(response.json.get("id"))

        self.assertEqual(len(response.json.get("attendees")), 1)
        self.assertEqual(len(response.json.get("looks")), 1)
        self.assertEqual(len(response.json.get("roles")), 3)

        response_attendee = response.json.get("attendees")[0]
        self.assertEqual(response_attendee.get("id"), str(attendee1.id))
        self.assertEqual(response_attendee.get("user").get("email"), attendee_user1.email)
        self.assertEqual(response_attendee.get("look_id"), str(attendee1.look_id))
        self.assertEqual(response_attendee.get("look").get("id"), str(look1.id))
        self.assertEqual(response_attendee.get("role_id"), str(role1.id))
        self.assertEqual(response_attendee.get("role").get("id"), str(role1.id))
        self.assertEqual(response_attendee.get("tracking")[0].get("tracking_number"), "123123")
        self.assertTrue("777" in response_attendee.get("tracking")[0].get("tracking_url", ""))

        response_look = response.json.get("looks")[0]
        self.assertEqual(response_look.get("id"), str(look1.id))
        self.assertEqual(response_look.get("name"), look1.name)

        reponse_role = response.json.get("roles")[2]
        self.assertEqual(reponse_role.get("id"), str(role1.id))
        self.assertEqual(reponse_role.get("name"), role1.name)

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

    def test_get_event_enriched_shows_owner_attendee_on_top(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        guest1 = self.user_service.create_user(fixtures.create_user_request())
        guest2 = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=owner.id))
        attendee1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=guest1.email)
        )
        attendee2 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=owner.email)
        )
        attendee3 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=guest2.email)
        )

        # when
        response = self.client.open(
            f"/events/{event.id}",
            query_string={**self.hmac_query_params.copy(), "enriched": True},
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json.get("attendees")[0].get("user_id"), str(owner.id))
        self.assertTrue(response.json.get("attendees")[0].get("is_owner"))
        self.assertFalse(response.json.get("attendees")[1].get("is_owner"))
        self.assertFalse(response.json.get("attendees")[2].get("is_owner"))

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
        self.assertEqual(len(response.json), 4)
        response_role1 = response.json[2]
        response_role2 = response.json[3]
        self.assertEqual(response_role1.get("id"), str(role1.id))
        self.assertEqual(response_role1.get("name"), role1.name)
        self.assertEqual(response_role2.get("id"), str(role2.id))
        self.assertEqual(response_role2.get("name"), role2.name)

    def test_get_roles_but_only_one_active(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        role1 = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        self.role_service.create_role(fixtures.create_role_request(event_id=event.id, is_active=False))

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
        self.assertEqual(len(response.json), 3)
        response_role = response.json[2]
        self.assertEqual(response_role.get("id"), str(role1.id))
        self.assertEqual(response_role.get("name"), role1.name)

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

    def test_get_attendees_for_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
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
        self.assertIsNotNone(response_attendee1["user"])
        self.assertIsNotNone(response_attendee2["user"])

    def test_get_attendees_for_event_without_users(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_request = fixtures.create_attendee_request(event_id=event.id, email=None)
        attendee = self.attendee_service.create_attendee(attendee_request)

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
        self.assertEqual(len(response.json), 1)
        response_attendee = response.json[0]
        self.assertEqual(str(attendee.id), response_attendee["id"])
        self.assertIsNotNone(response_attendee["user"])

    def test_attendees_for_non_existing_event(self):
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

    def test_delete_event_attendees_are_not_invited_or_paid(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user1.email)
        )
        attendee_user2 = self.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user2.email)
        )

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

        db_attendee1 = db.session.execute(select(Attendee).filter(Attendee.id == attendee1.id)).scalars().first()
        self.assertEqual(db_attendee1.is_active, False)
        db_attendee2 = db.session.execute(select(Attendee).filter(Attendee.id == attendee2.id)).scalars().first()
        self.assertEqual(db_attendee2.is_active, False)

    def test_delete_event_attendee_is_not_active(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email, is_active=False)
        )

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

        db_attendee = db.session.execute(select(Attendee).filter(Attendee.id == attendee.id)).scalars().first()
        self.assertEqual(db_attendee.is_active, False)

    def test_delete_event_attendee_is_not_active_but_invited(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email, is_active=False)
        )

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

        db_attendee = db.session.execute(select(Attendee).filter(Attendee.id == attendee.id)).scalars().first()
        self.assertEqual(db_attendee.is_active, False)

    def test_delete_event_attendee_is_invited(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email, invite=True)
        )

        # when
        response = self.client.open(
            f"/events/{event.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assertStatus(response, 400)
        self.assertEqual(response.json["errors"], "Cannot delete event with invited or paid attendees.")

    def test_delete_event_attendee_is_paid(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email, pay=True)
        )

        # when
        response = self.client.open(
            f"/events/{event.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assertStatus(response, 400)
        self.assertEqual(response.json["errors"], "Cannot delete event with invited or paid attendees.")

    def test_delete_event_attendee_paid_but_force_applied(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email, pay=True)
        )

        # when
        response = self.client.open(
            f"/events/{event.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            content_type=self.content_type,
            headers={**self.request_headers, FORCE_DELETE_HEADER: "true"},
        )

        # then
        self.assertStatus(response, 204)

    def test_delete_event_at_least_one_attendee_invite(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user1.email, invite=False)
        )
        attendee_user2 = self.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user2.email, invite=True)
        )
        attendee_user3 = self.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user3.email, invite=False)
        )

        # when
        response = self.client.open(
            f"/events/{event.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assertStatus(response, 400)
        self.assertEqual(response.json["errors"], "Cannot delete event with invited or paid attendees.")

    def test_delete_event_attendee_is_invited_but_if_force_applied_then_it_is_ok(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email, invite=True)
        )

        # when
        response = self.client.open(
            f"/events/{event.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            content_type=self.content_type,
            headers={**self.request_headers, FORCE_DELETE_HEADER: "true"},
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
