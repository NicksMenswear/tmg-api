from datetime import datetime, timedelta

from server.tests.integration import BaseTestCase, fixtures


class TestAddExpeditedShippingForSuitBundles(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.populate_shopify_variants()

    def test_no_event_that_expires_within_n_weeks(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(
            fixtures.create_event_request(
                user_id=user.id,
                event_at=(
                    datetime.now() + timedelta(weeks=self.app.config["NUM_WEEKS_ALLOWED_FOR_FREE_SHIPPING"] + 5)
                ).isoformat(),
            )
        )
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id, email=attendee_user.email, role_id=role.id, look_id=look.id
            )
        )

        # when
        response = self.client.open(
            "/jobs/add-expedited-shipping-for-suit-bundles",
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=None,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_event_within_expedited_range(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(
            fixtures.create_event_request(
                user_id=user.id,
                event_at=(datetime.now() + timedelta(weeks=3)).isoformat(),
            ),
            ignore_event_date_creation_condition=True,
        )
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        self.assertIsNone(look.product_specs.get("requires_expedited_shipping"))
        role = self.role_service.create_role(fixtures.create_role_request(event_id=event.id))
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id, email=attendee_user.email, role_id=role.id, look_id=look.id
            )
        )

        # when
        response = self.client.open(
            "/jobs/add-expedited-shipping-for-suit-bundles",
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=None,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]["id"], str(look.id))
        self.assertTrue(response.json[0]["product_specs"]["requires_expedited_shipping"])

    def test_multiple_events_within_expedited_range(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event1 = self.event_service.create_event(
            fixtures.create_event_request(
                user_id=user.id,
                event_at=(datetime.now() + timedelta(weeks=3)).isoformat(),
            ),
            ignore_event_date_creation_condition=True,
        )
        event2 = self.event_service.create_event(
            fixtures.create_event_request(
                user_id=user.id,
                event_at=(datetime.now() + timedelta(weeks=4)).isoformat(),
            ),
            ignore_event_date_creation_condition=True,
        )
        attendee_user1 = self.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.user_service.create_user(fixtures.create_user_request())
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user1.id, product_specs=self.create_look_test_product_specs())
        )
        role1 = self.role_service.create_role(fixtures.create_role_request(event_id=event1.id))
        look2 = self.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user3.id, product_specs=self.create_look_test_product_specs())
        )
        role2 = self.role_service.create_role(fixtures.create_role_request(event_id=event2.id))
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event1.id, email=attendee_user1.email, role_id=role1.id, look_id=look1.id
            )
        )
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event1.id, email=attendee_user2.email, role_id=role1.id, look_id=look1.id
            )
        )
        self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event2.id, email=attendee_user3.email, role_id=role2.id, look_id=look2.id
            )
        )

        # when
        response = self.client.open(
            "/jobs/add-expedited-shipping-for-suit-bundles",
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=None,
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assertTrue(response.json[0]["id"] in {str(look1.id), str(look2.id)})
        self.assertTrue(response.json[1]["id"] in {str(look1.id), str(look2.id)})
        self.assertTrue(response.json[0]["product_specs"]["requires_expedited_shipping"])
        self.assertTrue(response.json[1]["product_specs"]["requires_expedited_shipping"])
