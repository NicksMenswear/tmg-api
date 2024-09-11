from __future__ import absolute_import

import json
import random
import uuid

from parameterized import parameterized

from server import encoder
from server.database.models import DiscountType
from server.models.event_model import EventUserStatus
from server.models.user_model import CreateUserModel, UserModel
from server.services.discount_service import GIFT_DISCOUNT_CODE_PREFIX
from server.services.user_service import MAX_NAME_LENGTH
from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures


class TestUsers(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.populate_shopify_variants(100)

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
            data=json.dumps(create_user.model_dump(), cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(create_user.first_name, response.json["first_name"])
        self.assertEqual(create_user.last_name, response.json["last_name"])
        self.assertEqual(create_user.email, response.json["email"])
        self.assertIsNotNone(response.json["id"])

    def test_create_user_with_existing_but_capitalized_email(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(
                fixtures.create_user_request(email=user.email.capitalize()).model_dump(), cls=encoder.CustomJSONEncoder
            ),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 409)

    def test_update_non_existing_user(self):
        # when
        response = self.client.open(
            f"/users/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(fixtures.create_user_request().model_dump(), cls=encoder.CustomJSONEncoder),
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
        updated_email = utils.generate_email()

        updated_user = fixtures.update_user_request(
            first_name=updated_first_name, last_name=updated_last_name, email=updated_email
        )

        response = self.client.open(
            f"/users/{str(user.id)}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=json.dumps(updated_user.model_dump(), cls=encoder.CustomJSONEncoder),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(str(user.id), response.json["id"])
        self.assertEqual(updated_user.email, response.json["email"])
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
        self.assertEqual(response.json[0]["name"], str(event1.name))
        self.assertEqual(response.json[1]["id"], str(event2.id))
        self.assertEqual(response.json[1]["name"], str(event2.name))

    def test_get_all_events_for_user_owned_and_enriched(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        event1 = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        role11 = self.role_service.create_role(fixtures.create_role_request(event_id=event1.id))
        self.role_service.create_role(fixtures.create_role_request(event_id=event1.id, is_active=False))
        attendee_user1 = self.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event1.id, email=attendee_user1.email)
        )
        attendee_user2 = self.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event1.id, email=attendee_user2.email)
        )
        attendee_user3 = self.user_service.create_user(fixtures.create_user_request())
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event1.id, email=attendee_user3.email, is_active=False)
        )
        not_used_paid_discount = self.app.discount_service.create_discount(
            event1.id,
            attendee1.id,
            random.randint(50, 200),
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )
        used_paid_discount = self.app.discount_service.create_discount(
            event1.id,
            attendee1.id,
            random.randint(50, 200),
            DiscountType.GIFT,
            True,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )
        self.app.discount_service.create_discount(
            event1.id,
            attendee1.id,
            random.randint(50, 200),
            DiscountType.GIFT,
        )

        event2 = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        self.event_service.create_event(fixtures.create_event_request(user_id=user.id, is_active=False))

        # when
        response = self.client.open(
            f"/users/{user.id}/events",
            query_string={**self.hmac_query_params, "enriched": True},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 2)

        response_event1 = response.json[0]
        self.assertEqual(response_event1["id"], str(event1.id))
        self.assertEqual(response_event1["status"], str(EventUserStatus.OWNER))
        self.assertEqual(len(response_event1["roles"]), 3)
        self.assertEqual(response_event1["roles"][2]["id"], str(role11.id))
        self.assertEqual(len(response_event1["looks"]), 1)
        self.assertEqual(response_event1["looks"][0]["id"], str(look.id))
        self.assertEqual(len(response_event1["attendees"]), 2)

        response_attendee1 = response_event1["attendees"][0]
        self.assertEqual(response_attendee1["id"], str(attendee1.id))
        self.assertEqual(response_attendee1["user"]["email"], str(attendee_user1.email))
        self.assertFalse(response_attendee1["can_be_deleted"])
        gift_codes1 = response_attendee1["gift_codes"]
        self.assertEqual(len(gift_codes1), 2)
        self.assertEqual(
            {gift_codes1[0]["code"], gift_codes1[1]["code"]},
            {not_used_paid_discount.shopify_discount_code, used_paid_discount.shopify_discount_code},
        )

        response_attendee2 = response_event1["attendees"][1]
        self.assertEqual(response_attendee2["id"], str(attendee2.id))
        self.assertEqual(response_attendee2["user"]["email"], str(attendee_user2.email))
        self.assertTrue(response_attendee2["can_be_deleted"])

        response_event2 = response.json[1]
        self.assertEqual(response_event2["id"], str(event2.id))
        self.assertEqual(response_event2["status"], str(EventUserStatus.OWNER))
        self.assertEqual(len(response_event2["roles"]), 2)
        self.assertEqual(response_event2["looks"][0]["id"], str(look.id))
        self.assertEqual(len(response_event2["attendees"]), 0)

    def test_get_all_events_for_user_invited_and_enriched(self):
        # given
        user1 = self.user_service.create_user(fixtures.create_user_request())
        event1 = self.event_service.create_event(fixtures.create_event_request(user_id=user1.id))
        user2 = self.user_service.create_user(fixtures.create_user_request())
        event2 = self.event_service.create_event(fixtures.create_event_request(user_id=user2.id))
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user1.id, product_specs=self.create_look_test_product_specs())
        )
        look2 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user2.id, product_specs=self.create_look_test_product_specs())
        )
        role11 = self.role_service.create_role(fixtures.create_role_request(event_id=event1.id))
        self.role_service.create_role(fixtures.create_role_request(event_id=event1.id, is_active=False))
        role21 = self.role_service.create_role(fixtures.create_role_request(event_id=event2.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event1.id, email=attendee_user.email, look_id=look1.id, role_id=role11.id, invite=True
            )
        )
        # adding attendee and removing it
        attendee3 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event2.id, email=attendee_user.email, look_id=look2.id, role_id=role21.id, invite=True
            )
        )
        self.attendee_service.delete_attendee(attendee3.id)
        attendee2 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event2.id, email=attendee_user.email, look_id=look2.id, role_id=role21.id, invite=True
            )
        )

        # when
        response = self.client.open(
            f"/users/{attendee_user.id}/events",
            query_string={**self.hmac_query_params, "enriched": True},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 2)

        response_event1 = response.json[0]
        self.assertEqual(response_event1["id"], str(event1.id))
        self.assertEqual(len(response_event1["attendees"]), 1)
        response_attendee1 = response_event1["attendees"][0]
        self.assertEqual(response_attendee1["id"], str(attendee1.id))
        self.assertEqual(response_attendee1["look"]["id"], str(look1.id))
        self.assertEqual(response_attendee1["role"]["id"], str(role11.id))
        self.assertEqual(response_attendee1["user"]["email"], str(attendee_user.email))

        response_event2 = response.json[1]
        self.assertEqual(response_event2["id"], str(event2.id))
        self.assertEqual(len(response_event2["attendees"]), 1)
        response_attendee2 = response_event2["attendees"][0]
        self.assertEqual(response_attendee2["id"], str(attendee2.id))
        self.assertEqual(response_attendee2["look"]["id"], str(look2.id))
        self.assertEqual(response_attendee2["role"]["id"], str(role21.id))
        self.assertEqual(response_attendee2["user"]["email"], str(attendee_user.email))

    def test_get_all_events_for_user_invited(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.user_service.create_user(fixtures.create_user_request())
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user1.email, invite=True)
        )
        attendee2 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user2.email, invite=True)
        )
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user3.email, invite=True)
        )

        # when
        response = self.client.open(
            f"/users/{attendee_user2.id}/events",
            query_string={**self.hmac_query_params, "enriched": True, "status": "attendee"},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 1)

        response_event = response.json[0]
        self.assertEqual(response_event["id"], str(event.id))
        self.assertEqual(len(response_event["attendees"]), 1)
        response_attendee = response_event["attendees"][0]
        self.assertEqual(response_attendee["id"], str(attendee2.id))
        self.assertEqual(response_attendee["user"]["email"], str(attendee_user2.email))

    def test_get_events_where_user_is_invited(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event1 = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        event2 = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event1.id, email=attendee_user.email, invite=True)
        )
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event2.id, email=attendee_user.email, invite=False)
        )

        # when
        response = self.client.open(
            f"/users/{attendee_user.id}/events",
            query_string={**self.hmac_query_params, "enriched": True, "status": "attendee"},
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 1)

        response_event = response.json[0]
        self.assertEqual(response_event["id"], str(event1.id))
        self.assertEqual(len(response_event["attendees"]), 1)
        response_attendee = response_event["attendees"][0]
        self.assertEqual(response_attendee["id"], str(attendee1.id))
        self.assertEqual(response_attendee["user"]["email"], str(attendee_user.email))

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
            fixtures.create_attendee_request(event_id=event1.id, email=attendee_user.email, invite=True)
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
            fixtures.create_attendee_request(event_id=event1.id, email=attendee_user.email, invite=True)
        )
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event2.id, email=attendee_user.email, invite=True)
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
        self.event_service.create_event(fixtures.create_event_request(user_id=user2.id, is_active=False))
        self.event_service.create_event(fixtures.create_event_request(user_id=user1.id, is_active=False))
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event1.id, email=user2.email, invite=True)
        )

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
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user1.id, product_specs=self.create_look_test_product_specs())
        )
        look2 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user1.id, product_specs=self.create_look_test_product_specs())
        )
        self.look_service.create_look(
            fixtures.create_look_request(
                user_id=user1.id, is_active=False, product_specs=self.create_look_test_product_specs()
            )
        )
        self.look_service.create_look(
            fixtures.create_look_request(user_id=user2.id, product_specs=self.create_look_test_product_specs())
        )

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
        self.assertEqual(response_look1["name"], str(look1.name))
        self.assertEqual(response_look1["price"], self.look_service.get_look_price(look1))
        self.assertEqual(response_look2["id"], str(look2.id))
        self.assertEqual(response_look2["name"], str(look2.name))
        self.assertEqual(response_look2["price"], self.look_service.get_look_price(look2))

    def test_create_user_first_name_too_long(self):
        # given
        email = utils.generate_email()
        first_name = utils.generate_unique_name(100, 100)

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(
                {"first_name": first_name, "last_name": "abcd", "email": email},
                cls=encoder.CustomJSONEncoder,
            ),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        saved_user = self.user_service.get_user_by_email(email)
        self.assertEqual(
            first_name[:MAX_NAME_LENGTH],
            saved_user.first_name,
        )

    def test_create_user_last_name_too_long(self):
        # given
        email = utils.generate_email()
        last_name = utils.generate_unique_name(100, 100)

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(
                {
                    "first_name": "abcd",
                    "last_name": last_name,
                    "email": email,
                },
                cls=encoder.CustomJSONEncoder,
            ),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        saved_user = self.user_service.get_user_by_email(email)
        self.assertEqual(
            last_name[:MAX_NAME_LENGTH],
            saved_user.last_name,
        )

    def test_create_user_first_name_is_none(self):
        # given
        email = utils.generate_email()

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(
                {"first_name": None, "last_name": "abcd", "email": email},
                cls=encoder.CustomJSONEncoder,
            ),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        saved_user = self.user_service.get_user_by_email(email)
        self.assertIsNone(saved_user.first_name)

    def test_create_user_last_name_is_none(self):
        # given
        email = utils.generate_email()

        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(
                {
                    "first_name": "abcd",
                    "last_name": None,
                    "email": email,
                },
                cls=encoder.CustomJSONEncoder,
            ),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        saved_user = self.user_service.get_user_by_email(email)
        self.assertIsNone(saved_user.last_name)

    @parameterized.expand(
        [
            ["Alejandro", "Muñoz Mendieta"],
            ["Hannah & Gabriel", "Geiger"],
            ["De’Aveone", "Smith"],
            ["A", "B"],
            ["Hannah, Gabriel", "Geiger"],  # comma
        ]
    )
    def test_create_with_special_characters(self, first_name, last_name):
        # when
        response = self.client.open(
            "/users",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": "test@example.com",
                },
                cls=encoder.CustomJSONEncoder,
            ),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)

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
