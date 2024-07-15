from __future__ import absolute_import

import json
import random
import uuid

from server import encoder
from server.database.models import DiscountType
from server.services.discount_service import (
    GIFT_DISCOUNT_CODE_PREFIX,
)
from server.tests.integration import BaseTestCase, fixtures


class TestDiscountsCreateDiscountIntent(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_create_for_non_active_event(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id, is_active=False))

        # when
        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [fixtures.create_gift_discount_intent_request(attendee_id=uuid.uuid4()).model_dump()],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert404(response)
        self.assertTrue("Event not found" in response.json["errors"])

    def test_create_for_invalid_event(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
        )

        # when
        response = self.client.open(
            f"/events/{str(uuid.uuid4())}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [
                    fixtures.create_gift_discount_intent_request(attendee_id=str(attendee.id)).model_dump(),
                ],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert404(response)
        self.assertTrue("Event not found" in response.json["errors"])

    def test_create_with_empty_intents_input(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert400(response)
        self.assertTrue("No discount intents provided" in response.json["errors"])

    def test_create_for_invalid_one_attendee(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )

        # when
        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [
                    fixtures.create_gift_discount_intent_request(
                        attendee_id=attendee.id
                    ).model_dump(),  # valid attendee_id
                    fixtures.create_gift_discount_intent_request(
                        attendee_id=uuid.uuid4()
                    ).model_dump(),  # invalid attendee_id
                ],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert404(response)
        self.assertTrue("Attendee not found" in response.json["errors"])

    def test_create_for_not_active_attendee(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, is_active=False)
        )

        # when
        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [
                    fixtures.create_gift_discount_intent_request(attendee_id=str(attendee.id)).model_dump(),
                ],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert404(response)
        self.assertTrue("Attendee not found" in response.json["errors"])

    def test_create_with_invalid_amount(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
        )

        # when
        discount_intent_request = fixtures.create_gift_discount_intent_request(
            attendee_id=str(attendee.id), amount=100
        ).model_dump()
        discount_intent_request["amount"] = -100

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps([discount_intent_request], cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assert400(response)
        self.assertEqual("Input should be greater than 0", response.json["errors"])

    def test_create_of_type_gift(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )

        # when
        created_discount_intent_request = fixtures.create_gift_discount_intent_request(
            attendee_id=attendee.id
        ).model_dump()

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [created_discount_intent_request],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        response_variant_id = response.json["variant_id"]
        self.assertIsNotNone(response_variant_id)

        discount_intents = self.discount_service.get_gift_discount_intents_for_product_variant(response_variant_id)
        self.assertEqual(len(discount_intents), 1)
        discount_intent = discount_intents[0]
        self.assertEqual(discount_intent.type.value, str(DiscountType.GIFT))
        self.assertEqual(discount_intent.event_id, event.id)
        self.assertEqual(discount_intent.amount, created_discount_intent_request["amount"])
        self.assertIsNotNone(discount_intent.id)
        self.assertEqual(discount_intent.attendee_id, attendee.id)

        shopify_virtual_product_variant = self.app.shopify_service.shopify_virtual_product_variants.get(
            response_variant_id
        )
        self.assertIsNotNone(shopify_virtual_product_variant)
        self.assertEqual(shopify_virtual_product_variant["price"], created_discount_intent_request["amount"])

    def test_create_of_type_gift_for_2_attendees(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user1.email, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user2.email, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )

        # when
        created_discount_intent_request1 = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee1.id))
        created_discount_intent_request2 = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee2.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [created_discount_intent_request1.model_dump(), created_discount_intent_request2.model_dump()],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        response_variant_id = response.json["variant_id"]
        self.assertIsNotNone(response_variant_id)

        discount_intents = self.discount_service.get_gift_discount_intents_for_product_variant(response_variant_id)
        self.assertEqual(len(discount_intents), 2)
        discount_intent1 = discount_intents[0]
        discount_intent2 = discount_intents[1]

        self.assertEqual(discount_intent1.type, DiscountType.GIFT)
        self.assertEqual(discount_intent1.event_id, event.id)
        self.assertEqual(discount_intent2.type, DiscountType.GIFT)
        self.assertEqual(discount_intent2.event_id, event.id)

        shopify_virtual_product_variant = self.app.shopify_service.shopify_virtual_product_variants.get(
            response_variant_id
        )
        self.assertIsNotNone(shopify_virtual_product_variant)
        self.assertEqual(
            shopify_virtual_product_variant["price"],
            created_discount_intent_request1.amount + created_discount_intent_request2.amount,
        )

    def test_create_for_party_of_4_but_only_one_attendee_has_intents_set(
        self,
    ):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user1.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user2.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user3.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user4.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )

        # when
        created_discount_intent_request1 = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee1.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [created_discount_intent_request1.model_dump()],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        response_variant_id = response.json["variant_id"]
        self.assertIsNotNone(response_variant_id)

        shopify_virtual_product_variant = self.app.shopify_service.shopify_virtual_product_variants.get(
            response_variant_id
        )
        self.assertIsNotNone(shopify_virtual_product_variant)
        self.assertEqual(shopify_virtual_product_variant["price"], created_discount_intent_request1.amount)

    def test_create_for_party_of_4(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user1.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user2.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user3.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user4.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )

        # when
        created_discount_intent_request1 = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee1.id))
        created_discount_intent_request2 = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee2.id))
        created_discount_intent_request3 = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee3.id))
        created_discount_intent_request4 = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee4.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [
                    created_discount_intent_request1.model_dump(),
                    created_discount_intent_request2.model_dump(),
                    created_discount_intent_request3.model_dump(),
                    created_discount_intent_request4.model_dump(),
                ],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        response_variant_id = response.json["variant_id"]
        self.assertIsNotNone(response_variant_id)

        shopify_virtual_product_variant = self.app.shopify_service.shopify_virtual_product_variants.get(
            response_variant_id
        )
        self.assertIsNotNone(shopify_virtual_product_variant)
        self.assertEqual(
            shopify_virtual_product_variant["price"],
            created_discount_intent_request1.amount
            + created_discount_intent_request2.amount
            + created_discount_intent_request3.amount
            + created_discount_intent_request4.amount,
        )

    def test_create_for_attendee_that_already_has_discount_intent_of_type_gift_it_should_be_overwritten(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        self.app.discount_service.create_discount(event.id, attendee.id, 5, DiscountType.GIFT)

        # when
        created_discount_intent_request = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [created_discount_intent_request.model_dump()],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        response_variant_id = response.json["variant_id"]
        self.assertIsNotNone(response_variant_id)

        shopify_virtual_product_variant = self.app.shopify_service.shopify_virtual_product_variants.get(
            response_variant_id
        )
        self.assertIsNotNone(shopify_virtual_product_variant)
        self.assertEqual(shopify_virtual_product_variant["price"], created_discount_intent_request.amount)

    def test_create_for_attendee_that_already_has_discount_code_of_type_gift(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        existing_discount = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(1, 9),
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        created_discount_intent_request = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [created_discount_intent_request.model_dump()],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        response_variant_id = response.json["variant_id"]
        self.assertIsNotNone(response_variant_id)

        shopify_virtual_product_variant = self.app.shopify_service.shopify_virtual_product_variants.get(
            response_variant_id
        )
        self.assertIsNotNone(shopify_virtual_product_variant)
        self.assertEqual(shopify_virtual_product_variant["price"], created_discount_intent_request.amount)

        discounts = self.discount_service.get_discounts_by_attendee_id(attendee.id)
        self.assertEqual(len(discounts), 2)

        discount1 = discounts[0]
        discount2 = discounts[1]

        self.assertNotEqual(discount1.shopify_virtual_product_id, discount2.shopify_virtual_product_id)
        self.assertNotEqual(discount1.amount, discount2.amount)
        self.assertTrue(existing_discount.amount in [discount1.amount, discount2.amount])
        self.assertNotEqual(discount1.amount, discount2.amount)
        self.assertTrue(created_discount_intent_request.amount in [discount1.amount, discount2.amount])

    def test_create_for_attendee_with_no_invite(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user.id, event_id=event.id, look_id=look.id, invite=False, style=True
            )
        )

        # when
        created_discount_intent_request = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [created_discount_intent_request.model_dump()],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 400)
        self.assertTrue("Attendee is not invited" in response.json["errors"])

    def test_create_for_attendee_with_no_style(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user.id, event_id=event.id, look_id=look.id, invite=True, style=False
            )
        )

        # when
        created_discount_intent_request = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [created_discount_intent_request.model_dump()],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 400)
        self.assertTrue("Attendee is not styled" in response.json["errors"])

    def test_create_for_attendee_with_no_look(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user.id, event_id=event.id, look_id=None, invite=True, style=True
            )
        )

        # when
        created_discount_intent_request = fixtures.create_gift_discount_intent_request(attendee_id=str(attendee.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [created_discount_intent_request.model_dump()],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 400)
        self.assertTrue("Attendee has no look associated." in response.json["errors"])

    def test_create_intent_amount_bigger_then_look_price(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )

        # when
        created_discount_intent_request = fixtures.create_gift_discount_intent_request(
            attendee_id=str(attendee.id), amount=10000
        )

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [created_discount_intent_request.model_dump()],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 400)
        self.assertTrue("Pay amount exceeds look price" in response.json["errors"])

    def test_create_intent_amount_bigger_then_look_price_with_discount(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            self.app.look_service.get_look_price(look) - 20,
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        created_discount_intent_request = fixtures.create_gift_discount_intent_request(
            attendee_id=str(attendee.id), amount=random.randint(30, 100)
        )

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [created_discount_intent_request.model_dump()],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 400)
        self.assertTrue("Pay amount exceeds look price" in response.json["errors"])

    def test_create_intent_for_group_of_4_too_much(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        # hack to reduce price of the look so smaller discount is applied
        self.shopify_service.shopify_variants.get(
            look.product_specs["bundle"]["variant_id"]
        ).variant_price = random.randint(200, 299)
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user1.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user2.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user3.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user4.id, event_id=event.id, look_id=look.id, style=True, invite=True
            )
        )

        # when
        created_discount_intent_request = fixtures.create_gift_discount_intent_request(
            attendee_id=str(attendee1.id), amount=250
        )

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [created_discount_intent_request.model_dump()],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 400)
        self.assertTrue("Pay amount exceeds look price" in response.json["errors"])
