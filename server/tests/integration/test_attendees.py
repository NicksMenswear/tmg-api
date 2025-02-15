from __future__ import absolute_import

import json
import random
import uuid

from server.controllers import FORCE_DELETE_HEADER
from server.database.database_manager import db
from server.database.models import DiscountType, Attendee, User
from server.models.shopify_model import ShopifyCustomer
from server.services.discount_service import GIFT_DISCOUNT_CODE_PREFIX, TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX
from server.services.integrations.shopify_service import ShopifyService
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

        # checking db
        db_user = db.session.query(User).filter(User.email == create_attendee.email).first()
        self.assertIsNone(db_user)

    def test_create_attendee_with_email_that_is_already_added_to_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_email = utils.generate_email()
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, email=attendee_email))

        # when
        create_attendee = fixtures.create_attendee_request(event_id=event.id, email=attendee_email)

        response = self.client.open(
            "/attendees",
            query_string=self.hmac_query_params,
            method="POST",
            data=create_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 409)
        self.assertEqual(response.json["errors"], "Attendee with this email already exists.")

    def test_create_attendee_with_email_that_is_already_added_to_event_but_the_other_not_active_which_is_ok(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_email = utils.generate_email()
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_email, is_active=False)
        )

        # when
        create_attendee = fixtures.create_attendee_request(event_id=event.id, email=attendee_email)

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

    def test_update_attendee_with_email_by_setting_same_email(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=owner.id))
        attendee_email = utils.generate_email()
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_email)
        )

        # when
        update_attendee = fixtures.update_attendee_request(email=attendee_email)

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

    def test_update_attendee_with_email_that_is_taken_by_other_attendee(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=owner.id))
        attendee1 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee2 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))

        # when
        update_attendee = fixtures.update_attendee_request(email=attendee1.email)

        response = self.client.open(
            f"/attendees/{attendee2.id}",
            query_string=self.hmac_query_params,
            method="PUT",
            data=update_attendee.json(),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 409)
        self.assertEqual(response.json["errors"], "Attendee with this email already exists.")

    def test_update_attendee_email_once_invite_was_sent(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=owner.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email, invite=True)
        )

        # when
        self.assertTrue(attendee.invite)
        self.assertIsNotNone(attendee.user_id)

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
        self.assertFalse(attendee_response.get("invite"))
        self.assertIsNone(attendee_response.get("user_id"))
        self.assertEqual(attendee_response["first_name"], attendee.first_name)
        self.assertEqual(attendee_response["last_name"], attendee.last_name)
        self.assertEqual(attendee_response["email"], update_attendee.email)

    def test_update_attendee_email_once_paid(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=owner.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email, invite=True, pay=True)
        )

        # when
        self.assertTrue(attendee.invite)
        self.assertTrue(attendee.pay)
        self.assertIsNotNone(attendee.user_id)

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
        self.assertStatus(response, 400)
        self.assertEqual(
            response.json["errors"],
            "Cannot update email for attendee that has already paid or has an issued gift code.",
        )

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

    def test_invites_no_attendees_passed(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        response = self.client.open(
            f"/invites",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps([]),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)

    def test_invites_attendee(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email)
        )

        # when
        db_attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertFalse(db_attendee.invite)

        response = self.client.open(
            f"/invites",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps([str(attendee.id)]),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)

        db_attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertTrue(db_attendee.invite)

        self.assertTrue(attendee_user.id not in self.email_service.sent_activations)
        self.assertTrue(attendee_user.id in self.email_service.sent_invites.get(event.id, set()))

    def test_invites_attendee_inactive(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_user.email, is_active=False)
        )

        # when
        db_attendee = self.attendee_service.get_attendee_by_id(attendee.id, False)
        self.assertFalse(db_attendee.invite)

        response = self.client.open(
            f"/invites",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps([str(attendee.id)]),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)

        db_attendee = self.attendee_service.get_attendee_by_id(attendee.id, False)
        self.assertFalse(db_attendee.invite)

        self.assertTrue(attendee_user.id not in self.email_service.sent_activations)
        self.assertTrue(attendee_user.id not in self.email_service.sent_invites.get(event.id, set()))

    def test_invites_multiple_attendees(self):
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
        db_attendee1 = self.attendee_service.get_attendee_by_id(attendee1.id)
        self.assertFalse(db_attendee1.invite)
        db_attendee2 = self.attendee_service.get_attendee_by_id(attendee2.id)
        self.assertFalse(db_attendee2.invite)

        response = self.client.open(
            f"/invites",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps([str(attendee1.id), str(attendee2.id)]),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)

        db_attendee1 = self.attendee_service.get_attendee_by_id(attendee1.id)
        self.assertTrue(db_attendee1.invite)
        db_attendee2 = self.attendee_service.get_attendee_by_id(attendee2.id)
        self.assertTrue(db_attendee2.invite)

        self.assertTrue(attendee_user1.id not in self.email_service.sent_activations)
        self.assertTrue(attendee_user2.id not in self.email_service.sent_activations)
        self.assertTrue(attendee_user1.id in self.email_service.sent_invites.get(event.id, set()))
        self.assertTrue(attendee_user2.id in self.email_service.sent_invites.get(event.id, set()))

    def test_invites_attendee_without_email(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=None)
        )

        # when
        db_attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertFalse(db_attendee.invite)

        response = self.client.open(
            f"/invites",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps([str(attendee.id)]),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)

        db_attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertFalse(db_attendee.invite)

    def test_invites_invalid_attendee_id(self):
        # when
        response = self.client.open(
            f"/invites",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps([str(uuid.uuid4())]),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)

    def test_invites_user_exist_but_not_associated_to_attendee(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=None)
        )

        # when
        db_attendee = Attendee.query.filter(Attendee.id == attendee.id).first()
        db_attendee.email = attendee_user.email
        db.session.commit()

        self.assertFalse(db_attendee.invite)

        response = self.client.open(
            f"/invites",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps([str(attendee.id)]),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)

        db_attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertTrue(db_attendee.invite)

        self.assertTrue(attendee_user.id not in self.email_service.sent_activations)
        self.assertTrue(attendee_user.id in self.email_service.sent_invites.get(event.id, set()))

    def test_invite_attendee_for_the_user_that_exists_in_shopify_but_not_in_our_db(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        email = f"{uuid.uuid4()}@shopify-user-exists.com"
        shopify_customer = ShopifyCustomer(
            gid=ShopifyService.customer_gid(random.randint(1000, 100000)),
            email=email,
            first_name=utils.generate_unique_name(),
            last_name=utils.generate_unique_name(),
            state="enabled",
        )
        self.shopify_service.customers[shopify_customer.gid] = shopify_customer
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=email)
        )

        # when
        response = self.client.open(
            f"/invites",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps([str(attendee.id)]),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)
        new_user = self.user_service.get_user_by_email(email)
        self.assertEqual(attendee.first_name, new_user.first_name)
        self.assertEqual(attendee.last_name, new_user.last_name)
        self.assertEqual(attendee.email, new_user.email)

    def test_invites_user_by_attendee_email(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_email = utils.generate_email()
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, email=attendee_email)
        )

        # when
        db_user = User.query.filter(User.email == attendee_email).first()
        self.assertIsNone(db_user)

        response = self.client.open(
            f"/invites",
            query_string=self.hmac_query_params,
            method="POST",
            data=json.dumps([str(attendee.id)]),
            headers=self.request_headers,
            content_type=self.content_type,
        )

        # then
        self.assertStatus(response, 201)

        db_attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertTrue(db_attendee.invite)

        db_user = User.query.filter(User.email == attendee_email).first()
        self.assertIsNotNone(db_user)

        self.assertTrue(db_attendee.user_id == db_user.id)
        self.assertEqual(db_user.first_name, db_attendee.first_name)
        self.assertEqual(db_user.last_name, db_attendee.last_name)
        self.assertIsNotNone(db_user.shopify_id)
        self.assertFalse(db_user.account_status)

        self.assertTrue(db_user.id not in self.email_service.sent_activations)
        self.assertTrue(db_user.id in self.email_service.sent_invites[event.id])
