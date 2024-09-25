from __future__ import absolute_import

import random
import uuid

from server.controllers import FORCE_DELETE_HEADER
from server.database.models import DiscountType
from server.services.discount_service import GIFT_DISCOUNT_CODE_PREFIX, TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX
from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures


class TestAttendees(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.populate_shopify_variants()

    def test_create_attendee(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        create_attendee = fixtures.create_attendee_request(event_id=event.id)

        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=create_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])
        self.assertIsNone(response.json["role_id"])
        self.assertIsNone(response.json["look_id"])
        self.assertEqual(str(create_attendee.event_id), response.json["event_id"])
        self.assertEqual(create_attendee.first_name, response.json["first_name"])
        self.assertEqual(create_attendee.last_name, response.json["last_name"])
        self.assertEqual(create_attendee.email, response.json["email"])
        self.assertIsNone(response.json["user_id"])

    def test_create_attendee_without_email(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        create_attendee_request = fixtures.create_attendee_request(event_id=event.id, email=None)

        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=create_attendee_request.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])
        self.assertEqual(str(event.id), response.json["event_id"])
        self.assertEqual(create_attendee_request.first_name, response.json["first_name"])
        self.assertEqual(create_attendee_request.last_name, response.json["last_name"])
        self.assertIsNone(create_attendee_request.email, response.json["email"])
        self.assertIsNone(response.json["user_id"])

    def test_create_attendee_without_role_and_look(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        create_attendee = fixtures.create_attendee_request(event_id=event.id, role_id=None, look_id=None)

        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=create_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])
        self.assertIsNone(response.json["role_id"])
        self.assertIsNone(response.json["look_id"])

    def test_create_attendee_without_role(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )

        # when
        create_attendee = fixtures.create_attendee_request(event_id=event.id, role_id=None, look_id=look.id)

        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=create_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNone(response.json.get("role_id"))
        self.assertIsNotNone(response.json["look_id"])
        self.assertEqual(response.json["look_id"], str(look.id))

    def test_create_attendee_without_look(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))

        # when
        create_attendee = fixtures.create_attendee_request(event_id=event.id, role_id=role.id)

        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=create_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNone(response.json.get("look_id"))
        self.assertIsNotNone(response.json["role_id"])
        self.assertTrue(response.json["role_id"], str(role.id))

    def test_create_attendee_for_existing_user(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        user2 = self.user_service.create_user(fixtures.create_user_request())

        # when
        create_attendee = fixtures.create_attendee_request(event_id=event.id, email=user2.email)

        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=create_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(str(user2.id), response.json["user_id"])
        self.assertEqual(create_attendee.first_name, response.json["first_name"])
        self.assertEqual(create_attendee.last_name, response.json["last_name"])
        self.assertEqual(create_attendee.email, response.json["email"])
        self.assertEqual(user2.email, response.json["email"])

    def test_create_attendee_for_existing_user_but_capitalized_email(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())

        # when
        create_attendee = fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email.capitalize())

        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=create_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(str(attendee_user.id), response.json["user_id"])

    def test_create_attendee_with_role_and_look(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))

        # when
        create_attendee = fixtures.create_attendee_request(event_id=event.id, role_id=role.id, look_id=look.id)

        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=create_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(response.json["role_id"], str(role.id))
        self.assertEqual(response.json["look_id"], str(look.id))

    def test_create_attendee_for_existing_attendee_user(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())

        # when
        create_attendee = fixtures.create_attendee_request(
            event_id=event.id,
            role_id=role.id,
            look_id=look.id,
            email=attendee_user.email,
            first_name=attendee_user.first_name,
            last_name=attendee_user.last_name,
        )

        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=create_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["role_id"])
        self.assertNotEqual(str(user.id), response.json["user_id"])
        self.assertEqual(str(attendee_user.id), response.json["user_id"])
        self.assertEqual(attendee_user.first_name, create_attendee.first_name)
        self.assertEqual(attendee_user.last_name, create_attendee.last_name)
        self.assertEqual(attendee_user.email, create_attendee.email)

    def test_create_attendee_but_it_already_exist_and_associated(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email)
        )

        # when
        new_attendee = fixtures.create_attendee_request(
            event_id=event.id,
            email=attendee_user.email,
            first_name=attendee_user.first_name,
            last_name=attendee_user.last_name,
        )

        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=new_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 409)

    def test_create_attendee_for_owner(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=owner.id))

        # when
        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=fixtures.create_attendee_request(event_id=event.id, email=owner.email).json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        self.assertTrue(response.json["invite"])

    def test_get_attendee_event_non_existing_user(self):
        # when
        query_params = {
            **self.hmac_query_params,
            "email": f"{str(uuid.uuid4())}@example.com",
            "event_id": str(uuid.uuid4()),
        }

        response = self.client.open(
            "/event_attendees",
            query_string=query_params,
            method="GET",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_update_attendee_name(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=owner.id))
        attendee = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))

        # when
        update_attendee = fixtures.update_attendee_request(
            first_name=utils.generate_unique_name(), last_name=utils.generate_unique_name()
        )

        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        attendee_response = response.json
        self.assertNotEqual(attendee_response["first_name"], attendee.first_name)
        self.assertNotEqual(attendee_response["last_name"], attendee.last_name)
        self.assertEqual(attendee_response["first_name"], update_attendee.first_name)
        self.assertEqual(attendee_response["last_name"], update_attendee.last_name)
        self.assertEqual(attendee_response["email"], attendee.email)

    def test_update_attendee_without_email_by_setting_email(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=owner.id))
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=None)
        )

        # when
        update_attendee = fixtures.update_attendee_request(email=utils.generate_email())

        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        attendee_response = response.json
        self.assertEqual(attendee_response["first_name"], attendee.first_name)
        self.assertEqual(attendee_response["last_name"], attendee.last_name)
        self.assertEqual(attendee_response["email"], update_attendee.email)

    def test_update_attendee_email(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=owner.id))
        attendee = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))

        # when
        update_attendee = fixtures.update_attendee_request(email=utils.generate_email())

        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        attendee_response = response.json
        self.assertEqual(attendee_response["first_name"], attendee.first_name)
        self.assertEqual(attendee_response["last_name"], attendee.last_name)
        self.assertEqual(attendee_response["email"], update_attendee.email)

    def test_update_attendee_email_once_invite_was_sent(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=owner.id))
        attendee = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))

        # when
        update_attendee = fixtures.update_attendee_request(email=utils.generate_email())

        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        attendee_response = response.json
        self.assertEqual(attendee_response["first_name"], attendee.first_name)
        self.assertEqual(attendee_response["last_name"], attendee.last_name)
        self.assertEqual(attendee_response["email"], update_attendee.email)

    def test_update_attendee_look_and_role(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=owner.id))
        user = self.user_service.create_user(fixtures.create_user_request())
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        role1 = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        look2 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        role2 = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id,
                email=user.email,
                role_id=role1.id,
                look_id=look1.id,
            )
        )

        # when
        update_attendee = fixtures.update_attendee_request(
            role_id=role2.id,
            look_id=look2.id,
        )

        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        attendee_response = response.json
        self.assertTrue(attendee_response["style"])
        self.assertFalse(attendee_response["invite"])
        self.assertFalse(attendee_response["pay"])
        self.assertFalse(attendee_response["size"])
        self.assertFalse(attendee_response["ship"])
        self.assertEqual(str(update_attendee.role_id), str(attendee_response["role_id"]))
        self.assertEqual(str(update_attendee.look_id), str(attendee_response["look_id"]))
        self.assertIsNotNone(attendee_response["id"])

        # checking db
        updated_attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertTrue(updated_attendee.style)
        self.assertFalse(updated_attendee.invite)
        self.assertFalse(updated_attendee.pay)
        self.assertFalse(updated_attendee.size)
        self.assertFalse(updated_attendee.ship)
        self.assertEqual(str(role2.id), str(updated_attendee.role_id))
        self.assertEqual(str(look2.id), str(updated_attendee.look_id))

    def test_update_attendee_role_can_not_be_removed_once_set(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id,
                email=user.email,
                role_id=role.id,
            )
        )

        # when
        update_attendee = fixtures.update_attendee_request(role_id=None)

        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        attendee_response = response.json
        self.assertEqual(str(role.id), str(attendee_response["role_id"]))

    def test_update_attendee_look_can_not_be_removed_once_set(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id,
                email=user.email,
                look_id=look.id,
            )
        )

        # when
        update_attendee = fixtures.update_attendee_request(look_id=None)

        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)
        attendee_response = response.json
        self.assertEqual(str(look.id), str(attendee_response["look_id"]))

    def test_update_attendee_can_not_update_look_once_paid(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        look2 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id,
                email=user.email,
                look_id=look1.id,
                pay=True,
            )
        )

        # when
        update_attendee = fixtures.update_attendee_request(look_id=look2.id)

        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 400)

    def test_update_attendee_can_not_update_look_when_gift_discount_code_issued(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        look2 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id,
                email=user.email,
                look_id=look1.id,
            )
        )
        not_used_paid_discount = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 200),
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        update_attendee = fixtures.update_attendee_request(look_id=look2.id)

        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 400)

    def test_update_attendee_update_look_when_just_gift_discount_intent_created(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        look2 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id,
                email=user.email,
                look_id=look1.id,
            )
        )
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 200),
            DiscountType.GIFT,
            False,
            None,
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        update_attendee = fixtures.update_attendee_request(look_id=look2.id)

        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)

    def test_update_attendee_update_look_when_just_group_discount_issued(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        look2 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id,
                email=user.email,
                look_id=look1.id,
            )
        )
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 200),
            DiscountType.PARTY_OF_FOUR,
            False,
            f"{TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        update_attendee = fixtures.update_attendee_request(look_id=look2.id)

        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 200)

    def test_update_attendee_non_existing(self):
        # when
        update_attendee = fixtures.update_attendee_request(
            role_id=None,
        )

        response = self.client.open(
            f"/attendees/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_delete_attendee(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=user.email, role_id=str(role.id), look_id=look.id)
        )

        # when
        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 204)

        # checking db
        soft_deleted_attendee = self.attendee_service.get_attendee_by_id(attendee.id, False)
        self.assertEqual(False, soft_deleted_attendee.is_active)

    def test_delete_attendee_with_invalid_id(self):
        # when
        response = self.client.open(
            f"/attendees/{str(uuid.uuid4())}",
            query_string=self.hmac_query_params,
            method="DELETE",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 404)

    def test_delete_attendee_that_paid_already(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id, email=user.email, role_id=str(role.id), look_id=look.id, pay=True
            )
        )

        # when
        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 400)

    def test_delete_attendee_that_paid_already_but_force_applied(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id, email=user.email, role_id=str(role.id), look_id=look.id, pay=True
            )
        )

        # when
        response = self.client.open(
            f"/attendees/{attendee.id}",
            query_string=self.hmac_query_params,
            method="DELETE",
            headers={**self.request_headers, FORCE_DELETE_HEADER: "true"},
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 204)
