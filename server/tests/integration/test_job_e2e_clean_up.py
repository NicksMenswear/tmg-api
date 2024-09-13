import random

from server.database.models import User, Attendee, DiscountType, Discount, Event, Role, Size, Measurement, Look
from server.services.discount_service import GIFT_DISCOUNT_CODE_PREFIX, TMG_GROUP_25_PERCENT_OFF_DISCOUNT_CODE_PREFIX
from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures


class TestJobE2ECleanUp(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_e2e_clean_up_no_customers(self):
        # when
        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        self.assertStatus(response, 200)

    def test_e2e_clean_up_single_user(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        self.shopify_service.customers[user.email] = {"id": random.randint(1000, 100000), "email": user.email}

        # when
        db_user = User.query.filter(User.email == user.email).first()
        shopify_customer = self.shopify_service.get_customer_by_email(user.email)
        self.assertIsNotNone(db_user)
        self.assertIsNotNone(shopify_customer)

        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        db_user = User.query.filter(User.email == user.email).first()
        self.assertIsNone(db_user)

        shopify_customer = self.shopify_service.get_customer_by_email(user.email)
        self.assertIsNone(shopify_customer)

        self.assertStatus(response, 200)

    def test_e2e_clean_up_multiple_users(self):
        # given
        user1 = self.user_service.create_user(fixtures.create_user_request())
        user2 = self.user_service.create_user(fixtures.create_user_request())
        user3 = self.user_service.create_user(fixtures.create_user_request())
        self.shopify_service.customers[user1.email] = {"id": random.randint(1000, 100000), "email": user1.email}
        self.shopify_service.customers[user2.email] = {"id": random.randint(1000, 100000), "email": user2.email}
        self.shopify_service.customers[user3.email] = {"id": random.randint(1000, 100000), "email": user3.email}

        # when
        db_user1 = User.query.filter(User.email == user1.email).first()
        db_user2 = User.query.filter(User.email == user2.email).first()
        db_user3 = User.query.filter(User.email == user3.email).first()
        shopify_customer1 = self.shopify_service.get_customer_by_email(user1.email)
        shopify_customer2 = self.shopify_service.get_customer_by_email(user2.email)
        shopify_customer3 = self.shopify_service.get_customer_by_email(user3.email)
        self.assertIsNotNone(db_user1)
        self.assertIsNotNone(db_user2)
        self.assertIsNotNone(db_user3)
        self.assertIsNotNone(shopify_customer1)
        self.assertIsNotNone(shopify_customer2)
        self.assertIsNotNone(shopify_customer3)

        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        db_user1 = User.query.filter(User.email == user1.email).first()
        db_user2 = User.query.filter(User.email == user2.email).first()
        db_user3 = User.query.filter(User.email == user3.email).first()
        self.assertIsNone(db_user1)
        self.assertIsNone(db_user2)
        self.assertIsNone(db_user3)

        shopify_customer1 = self.shopify_service.get_customer_by_email(user1.email)
        shopify_customer2 = self.shopify_service.get_customer_by_email(user2.email)
        shopify_customer3 = self.shopify_service.get_customer_by_email(user3.email)
        self.assertIsNone(shopify_customer1)
        self.assertIsNone(shopify_customer2)
        self.assertIsNone(shopify_customer3)

        self.assertStatus(response, 200)

    def test_e2e_clean_up_user_in_shopify_but_not_in_db(self):
        # given
        email = utils.generate_email()
        self.shopify_service.customers[email] = {"id": random.randint(1000, 100000), "email": email}

        # when
        shopify_customer = self.shopify_service.get_customer_by_email(email)
        self.assertIsNotNone(shopify_customer)

        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        shopify_customer = self.shopify_service.get_customer_by_email(email)
        self.assertIsNone(shopify_customer)

        self.assertStatus(response, 200)

    def test_e2e_clean_up_system_user_not_deleted(self):
        # given
        system_email = f"e2e+02@mail.dev.tmgcorp.net"
        user = self.user_service.create_user(fixtures.create_user_request(email=system_email))
        self.shopify_service.customers[user.email] = {"id": random.randint(1000, 100000), "email": user.email}

        # when
        db_user = User.query.filter(User.email == user.email).first()
        shopify_customer = self.shopify_service.get_customer_by_email(user.email)
        self.assertIsNotNone(db_user)
        self.assertIsNotNone(shopify_customer)

        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        db_user = User.query.filter(User.email == user.email).first()
        self.assertIsNotNone(db_user)

        shopify_customer = self.shopify_service.get_customer_by_email(user.email)
        self.assertIsNotNone(shopify_customer)

        self.assertStatus(response, 200)

    def test_e2e_clean_up_multiple_attendees(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        event1 = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        event2 = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event1.id, email=attendee_user.email)
        )
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event2.id, email=attendee_user.email)
        )
        self.shopify_service.customers[user.email] = {"id": random.randint(1000, 100000), "email": user.email}
        self.shopify_service.customers[attendee_user.email] = {
            "id": random.randint(1000, 100000),
            "email": attendee_user.email,
        }

        # when
        db_user = User.query.filter(User.email == user.email).first()
        db_attendees = Attendee.query.filter(Attendee.user_id == attendee_user.id).all()
        shopify_customer = self.shopify_service.get_customer_by_email(attendee_user.email)
        self.assertIsNotNone(db_user)
        self.assertIsNotNone(db_attendees[0])
        self.assertIsNotNone(db_attendees[1])
        self.assertIsNotNone(shopify_customer)

        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        db_user = User.query.filter(User.email == user.email).first()
        self.assertIsNone(db_user)

        db_attendee_users = Attendee.query.filter(Attendee.user_id == attendee_user.id).all()
        self.assertTrue(len(db_attendee_users) == 0)

        self.assertIsNone(self.shopify_service.get_customer_by_email(user.email))
        self.assertIsNone(self.shopify_service.get_customer_by_email(attendee_user.email))

        self.assertStatus(response, 200)

    def test_e2e_clean_up_attendees_with_multiple_discounts(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, email=attendee_user.email)
        )
        self.shopify_service.customers[user.email] = {"id": random.randint(1000, 100000), "email": user.email}
        self.shopify_service.customers[attendee_user.email] = {
            "id": random.randint(1000, 100000),
            "email": attendee_user.email,
        }
        discount1_gift = self.app.discount_service.create_discount(
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
        discount2_group = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 200),
            DiscountType.PARTY_OF_FOUR,
            False,
            f"{TMG_GROUP_25_PERCENT_OFF_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )
        discount_intent = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 200),
            DiscountType.GIFT,
        )

        # when
        self.assertIsNotNone(Discount.query.filter(Discount.id == discount1_gift.id).first())
        self.assertIsNotNone(Discount.query.filter(Discount.id == discount2_group.id).first())
        self.assertIsNotNone(Discount.query.filter(Discount.id == discount_intent.id).first())

        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        self.assertIsNone(Discount.query.filter(Discount.id == discount1_gift.id).first())
        self.assertIsNone(Discount.query.filter(Discount.id == discount2_group.id).first())
        self.assertIsNone(Discount.query.filter(Discount.id == discount_intent.id).first())

        self.assertStatus(response, 200)

    def test_e2e_clean_up_event(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, email=attendee_user.email)
        )
        self.shopify_service.customers[user.email] = {"id": random.randint(1000, 100000), "email": user.email}
        self.shopify_service.customers[attendee_user.email] = {
            "id": random.randint(1000, 100000),
            "email": attendee_user.email,
        }

        # when
        self.assertIsNotNone(Event.query.filter(Event.id == event.id).first())
        self.assertTrue(len(Role.query.filter(Role.event_id == event.id).all()) > 0)

        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        self.assertIsNone(Event.query.filter(Event.id == event.id).first())
        self.assertTrue(len(Role.query.filter(Role.event_id == event.id).all()) == 0)

        self.assertStatus(response, 200)

    def test_e2e_clean_up_sizes_and_measurements(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        measurement = self.measurement_service.create_measurement(fixtures.store_measurement_request(user_id=user.id))
        size = self.size_service.create_size(
            fixtures.store_size_request(user_id=str(user.id), measurement_id=measurement.id)
        )
        self.shopify_service.customers[user.email] = {"id": random.randint(1000, 100000), "email": user.email}

        # when
        self.assertIsNotNone(Measurement.query.filter(Measurement.id == measurement.id).first())
        self.assertIsNotNone(Size.query.filter(Size.id == size.id).first())

        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        self.assertIsNone(Measurement.query.filter(Measurement.id == measurement.id).first())
        self.assertIsNone(Size.query.filter(Size.id == size.id).first())

        self.assertStatus(response, 200)

    def test_e2e_clean_up_looks(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        look2 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        self.shopify_service.customers[user.email] = {"id": random.randint(1000, 100000), "email": user.email}

        # when
        self.assertIsNotNone(Look.query.filter(Look.id == look1.id).first())
        self.assertIsNotNone(Look.query.filter(Look.id == look2.id).first())

        response = self.client.open(
            "/jobs/system/e2e-clean-up",
            method="POST",
            query_string={},
            content_type=self.content_type,
            headers=self.request_headers,
            data={},
        )

        # then
        self.assertIsNone(Look.query.filter(Look.id == look1.id).first())
        self.assertIsNone(Look.query.filter(Look.id == look2.id).first())

        self.assertStatus(response, 200)
