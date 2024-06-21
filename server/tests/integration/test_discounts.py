from __future__ import absolute_import

import json
import random
import uuid

from server import encoder
from server.database.models import DiscountType
from server.services.discount import GIFT_DISCOUNT_CODE_PREFIX, TMG_GROUP_DISCOUNT_CODE_PREFIX, MIN_ORDER_AMOUNT
from server.tests.integration import BaseTestCase, fixtures


class TestDiscounts(BaseTestCase):
    def test_get_owner_discounts_for_invalid_event(self):
        # when
        response = self.client.open(
            f"/events/{str(uuid.uuid4())}/discounts",
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert404(response)
        self.assertTrue("Event not found" in response.json["errors"])

    def test_get_owner_discounts_from_event_without_attendees(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))

        # when
        response = self.client.open(
            f"/events/{event.id}/discounts",
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 0)

    def test_get_owner_discounts_from_event_with_attendees_and_looks_but_without_any_discounts(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        look1 = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user1.id, product_specs={"variants": [1234, 5678, 1715]})
        )
        look2 = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user2.id, product_specs={"variants": [9988, 1715]})
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user1.email, event_id=event.id, look_id=look1.id)
        )
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user2.email, event_id=event.id, look_id=look2.id)
        )
        attendees = [
            {"user": attendee_user1, "attendee": attendee1, "look": look1},
            {"user": attendee_user2, "attendee": attendee2, "look": look2},
        ]

        # when
        response = self.client.open(
            f"/events/{event.id}/discounts",
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 2)

        sorted_attendees = sorted(attendees, key=lambda x: str(x["attendee"].id))
        sorted_response_json = sorted(response.json, key=lambda x: str(x["attendee_id"]))

        attendee1 = sorted_attendees[0]
        attendee2 = sorted_attendees[1]
        discount_item1 = sorted_response_json[0]
        discount_item2 = sorted_response_json[1]

        self.assertEqual(discount_item1["attendee_id"], str(attendee1["attendee"].id))
        self.assertEqual(discount_item1["first_name"], attendee1["user"].first_name)
        self.assertEqual(discount_item1["last_name"], attendee1["user"].last_name)
        self.assertEqual(discount_item1["event_id"], str(event.id))
        self.assertEqual(discount_item1["user_id"], str(attendee1["user"].id))
        self.assertEqual(discount_item1["amount"], 0)
        self.assertEqual(len(discount_item1["gift_codes"]), 0)

        discount_status1 = discount_item1["status"]
        self.assertEqual(discount_status1["style"], attendee1["attendee"].style)
        self.assertEqual(discount_status1["pay"], attendee1["attendee"].pay)
        self.assertEqual(discount_status1["invite"], attendee1["attendee"].invite)

        discount_look1 = discount_item1["look"]
        self.assertEqual(discount_look1["id"], str(attendee1["look"].id))
        self.assertEqual(discount_look1["name"], attendee1["look"].name)

        self.assertEqual(discount_item2["attendee_id"], str(attendee2["attendee"].id))
        self.assertEqual(discount_item2["first_name"], attendee2["user"].first_name)
        self.assertEqual(discount_item2["last_name"], attendee2["user"].last_name)
        self.assertEqual(len(discount_item2["gift_codes"]), 0)
        self.assertEqual(discount_item2["event_id"], str(event.id))
        self.assertEqual(discount_item2["amount"], 0)
        self.assertEqual(discount_item2["user_id"], str(attendee2["user"].id))

        discount_status2 = discount_item2["status"]
        self.assertEqual(discount_status2["style"], attendee2["attendee"].style)
        self.assertEqual(discount_status2["pay"], attendee2["attendee"].pay)
        self.assertEqual(discount_status2["invite"], attendee2["attendee"].invite)

        discount_look2 = discount_item2["look"]
        self.assertEqual(discount_look2["id"], str(attendee2["look"].id))
        self.assertEqual(discount_look2["name"], attendee2["look"].name)

    def test_get_owner_discount_with_gift_codes_full_pay(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs={"variants": [1234, 5678, 1715]})
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user.email, event_id=event.id, look_id=look.id)
        )
        full_pay_discount = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 200),
            DiscountType.FULL_PAY,
            True,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        response = self.client.open(
            f"/events/{event.id}/discounts",
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 1)

        response_discount = response.json[0]

        self.assertEqual(response_discount["attendee_id"], str(attendee.id))
        self.assertEqual(len(response_discount["gift_codes"]), 1)

        gift_code = response_discount["gift_codes"][0]
        self.assertEqual(gift_code["code"], full_pay_discount.shopify_discount_code)
        self.assertEqual(gift_code["amount"], full_pay_discount.amount)
        self.assertEqual(gift_code["type"], full_pay_discount.type.value)
        self.assertTrue(gift_code["used"])

    def test_get_owner_discount_with_2_gift_codes_gift_one_paid_and_one_not_paid(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs={"variants": [1234, 5678, 1715]})
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user.email, event_id=event.id, look_id=look.id)
        )
        paid_discount = self.app.discount_service.create_discount(
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
        discount_intent = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 200),
            DiscountType.GIFT,
        )

        # when
        response = self.client.open(
            f"/events/{event.id}/discounts",
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
            headers=self.request_headers,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 1)

        response_discount = response.json[0]

        self.assertEqual(response_discount["attendee_id"], str(attendee.id))
        self.assertEqual(response_discount["amount"], discount_intent.amount)
        self.assertEqual(len(response_discount["gift_codes"]), 1)

        gift_code = response_discount["gift_codes"][0]
        self.assertEqual(gift_code["code"], paid_discount.shopify_discount_code)
        self.assertEqual(gift_code["amount"], paid_discount.amount)
        self.assertEqual(gift_code["type"], paid_discount.type.value)
        self.assertFalse(gift_code["used"])

    def test_create_discount_intent_for_non_active_event(self):
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

    def test_create_discount_intent_for_invalid_event(self):
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

    def test_create_discount_intent_with_empty_intents_input(self):
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

    def test_create_discount_intent_for_invalid_one_attendee(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
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

    def test_create_discount_intent_for_not_active_attendee(self):
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

    def test_create_discount_intent_both_amount_and_pay_full_missing(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
        )
        discount_intent_request = fixtures.create_gift_discount_intent_request(
            attendee_id=str(attendee.id)
        ).model_dump()
        del discount_intent_request["amount"]

        # when
        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [discount_intent_request],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 400)

    def test_create_discount_intent_with_invalid_amount(self):
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

    def test_create_discount_intent_of_type_gift(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user.email, event_id=event.id)
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

    def test_create_discount_intent_of_type_gift_for_2_attendees(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user1.email, event_id=event.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user2.email, event_id=event.id)
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

    def test_create_discount_intent_of_type_full_pay_look_not_set_for_attendee(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
        )

        # when
        created_discount_intent_request = fixtures.create_full_pay_discount_intent_request(attendee_id=attendee.id)

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
        self.assert404(response)
        self.assertTrue("Look not found" in response.json["errors"])

    def test_create_discount_intent_of_type_full_pay_look_has_no_variants(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(fixtures.create_look_request(user_id=attendee_user.id))
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )

        # when
        created_discount_intent_request = fixtures.create_full_pay_discount_intent_request(attendee_id=str(attendee.id))

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
        self.assertTrue("Look has no bundle associated" in response.json["errors"])

    def test_create_discount_intent_of_type_full_pay(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        variant1 = random.randint(30, 40)
        variant2 = random.randint(30, 50)
        variant3 = random.randint(30, 60)
        bundle_variant_id = variant1 + variant2 + variant3
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id,
                product_specs={"bundle": {"variant_id": bundle_variant_id}, "variants": [variant1, variant2, variant3]},
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )

        # when
        created_discount_intent_request = fixtures.create_full_pay_discount_intent_request(attendee_id=str(attendee.id))

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

        discount_intents = self.discount_service.get_gift_discount_intents_for_product_variant(response_variant_id)
        self.assertEqual(len(discount_intents), 1)
        discount_intent = discount_intents[0]
        self.assertEqual(discount_intent.type.value, str(DiscountType.FULL_PAY))
        self.assertEqual(discount_intent.event_id, event.id)
        discount_amount = (variant1 + variant2 + variant3) * 10
        self.assertEqual(discount_intent.amount, discount_amount)
        self.assertIsNotNone(discount_intent.id)
        self.assertEqual(discount_intent.attendee_id, attendee.id)

        shopify_virtual_product_variant = self.app.shopify_service.shopify_virtual_product_variants.get(
            response_variant_id
        )
        self.assertIsNotNone(shopify_virtual_product_variant)
        self.assertEqual(shopify_virtual_product_variant["price"], discount_amount)

    def test_create_discount_intent_of_type_full_pay_is_less_then_100(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        bundle_variant_id = random.randint(1, 9)
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id,
                product_specs={
                    "bundle": {"variant_id": bundle_variant_id},
                    "variants": [random.randint(10, 90), random.randint(10, 90)],
                },
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )

        # when
        created_discount_intent_request = fixtures.create_full_pay_discount_intent_request(attendee_id=str(attendee.id))

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
        self.assertTrue(f"Total look items price must be greater than {MIN_ORDER_AMOUNT}" in response.json["errors"])

    def test_create_discount_intent_of_mixed_types(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        variant1 = random.randint(30, 50)
        variant2 = random.randint(30, 60)
        bundle_variant_id = variant1 + variant2
        look1 = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user1.id,
                product_specs={"bundle": {"variant_id": bundle_variant_id}, "variants": [variant1, variant2]},
            )
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user1.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user2.id, event_id=event.id)
        )

        # when
        created_discount_intent_request1 = fixtures.create_full_pay_discount_intent_request(
            attendee_id=str(attendee1.id)
        )
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

        self.assertEqual(discount_intent1.event_id, event.id)
        self.assertEqual(discount_intent2.event_id, event.id)
        self.assertEqual({discount_intent1.type, discount_intent2.type}, {DiscountType.GIFT, DiscountType.FULL_PAY})

        total_amount = variant1 * 10 + variant2 * 10

        self.assertNotEqual(discount_intent1.amount, discount_intent2.amount)
        self.assertNotEqual(discount_intent1.type, discount_intent2.type)
        self.assertEqual(discount_intent1.type in [DiscountType.FULL_PAY, DiscountType.GIFT], True)
        self.assertEqual(discount_intent2.type in [DiscountType.FULL_PAY, DiscountType.GIFT], True)
        self.assertEqual(discount_intent1.amount in [total_amount, created_discount_intent_request2.amount], True)
        self.assertEqual(discount_intent2.amount in [total_amount, created_discount_intent_request2.amount], True)

        shopify_virtual_product_variant = self.app.shopify_service.shopify_virtual_product_variants.get(
            response_variant_id
        )
        self.assertIsNotNone(shopify_virtual_product_variant)
        self.assertEqual(
            shopify_virtual_product_variant["price"],
            discount_intent1.amount + discount_intent2.amount,
        )

    def test_create_discount_intent_for_party_of_4_of_type_gift_but_only_one_attendee_has_intents_set_no_tmg_discount_to_be_applied(
        self,
    ):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user1.id, event_id=event.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user2.id, event_id=event.id)
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user3.id, event_id=event.id)
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user4.id, event_id=event.id)
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

    def test_create_discount_intent_for_party_of_4_of_type_gift_no_tmg_discount_to_be_applied(
        self,
    ):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user1.id, event_id=event.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user2.id, event_id=event.id)
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user3.id, event_id=event.id)
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user4.id, event_id=event.id)
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

    def test_create_discount_intent_for_party_of_4_of_type_full_pay_but_only_one_attendee_has_intents_set_tmg_discount_of_100_off_to_be_applied(
        self,
    ):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        variant1 = random.randint(30, 40)
        variant2 = random.randint(30, 50)
        bundle_variant_id = variant1 + variant2
        look1 = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user1.id,
                product_specs={"bundle": {"variant_id": bundle_variant_id}, "variants": [variant1, variant2]},
            )
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user1.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user2.id, event_id=event.id)
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user3.id, event_id=event.id)
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user4.id, event_id=event.id)
        )

        # when
        created_discount_intent_request1 = fixtures.create_full_pay_discount_intent_request(
            attendee_id=str(attendee1.id)
        )

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
        self.assertEqual(
            shopify_virtual_product_variant["price"],
            variant1 * 10 + variant2 * 10 - 100,
        )

    def test_create_discount_intent_for_attendee_that_already_has_discount_intent_of_type_gift_it_should_be_overwritten(
        self,
    ):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
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

    def test_create_discount_intent_for_attendee_that_already_has_discount_code_of_type_gift(
        self,
    ):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
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

    def test_create_discount_intent_for_attendee_that_already_has_discount_code_of_type_full_pay(
        self,
    ):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
        )
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(300, 700),
            DiscountType.FULL_PAY,
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
        self.assertStatus(response, 400)
        self.assertTrue("Groom full pay gift discount already issued for attendee" in response.json["errors"])

    def test_create_discount_intent_of_type_full_pay_for_attendee_that_already_has_discount_code(
        self,
    ):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id, product_specs={"variants": [random.randint(10, 30), random.randint(10, 30)]}
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )
        self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(300, 700),
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        created_discount_intent_request = fixtures.create_full_pay_discount_intent_request(attendee_id=str(attendee.id))

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
        self.assertTrue("Groom gift discount already issued for attendee" in response.json["errors"])

    def test_apply_discounts_invalid_attendee(self):
        # when
        response = self.client.open(
            f"/attendees/{str(uuid.uuid4())}/apply-discounts",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.apply_discounts_request(event_id=uuid.uuid4()).model_dump(), cls=encoder.CustomJSONEncoder
            ),
        )

        # then
        self.assertStatus(response, 404)
        self.assertTrue("Attendee not found" in response.json["errors"])

    def test_apply_discounts_invalid_event(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
        )

        # when
        response = self.client.open(
            f"/attendees/{str(attendee.id)}/apply-discounts",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.apply_discounts_request(event_id=uuid.uuid4()).model_dump(), cls=encoder.CustomJSONEncoder
            ),
        )

        # then
        self.assertStatus(response, 404)
        self.assertTrue("Event not found" in response.json["errors"])

    ################################
    #    FIX ME
    ################################

    def test_apply_discounts_no_gift_discounts_and_party_less_then_4(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id)
        )

        # when
        response = self.client.open(
            f"/attendees/{str(attendee.id)}/apply-discounts",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.apply_discounts_request(event_id=event.id).model_dump(), cls=encoder.CustomJSONEncoder
            ),
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(response.json, [])

    def test_apply_discounts_no_gift_discounts_and_party_more_then_4(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        variant_id1 = 123
        variant_id2 = 234
        bundle_variant_id = variant_id1 + variant_id2
        look1 = self.look_service.create_look(
            fixtures.create_look_request(
                user_id=user.id,
                product_specs={"bundle": {"variant_id": bundle_variant_id}, "variants": [variant_id1, variant_id2]},
            )
        )
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user1.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user2.id, event_id=event.id)
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user3.id, event_id=event.id)
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user4.id, event_id=event.id)
        )

        # when
        response = self.client.open(
            f"/attendees/{str(attendee1.id)}/apply-discounts",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.apply_discounts_request(event_id=event.id).model_dump(), cls=encoder.CustomJSONEncoder
            ),
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 1)
        self.assertTrue(response.json[0].startswith(TMG_GROUP_DISCOUNT_CODE_PREFIX))

    def test_apply_discounts_with_gift_discounts(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs={"variants": [123, 234]})
        )
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )
        discount1 = self.app.discount_service.create_discount(
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
        discount2 = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(100, 400),
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )
        already_used_discount = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(100, 400),
            DiscountType.GIFT,
            True,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        response = self.client.open(
            f"/attendees/{str(attendee.id)}/apply-discounts",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.apply_discounts_request(event_id=event.id).model_dump(), cls=encoder.CustomJSONEncoder
            ),
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assertEqual(set(response.json), {discount1.shopify_discount_code, discount2.shopify_discount_code})

    def test_apply_discounts_with_gift_discounts_and_party_of_4(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        variant_id1 = 123
        variant_id2 = 234
        bundle_variant_id = variant_id1 + variant_id2
        look1 = self.look_service.create_look(
            fixtures.create_look_request(
                user_id=user.id,
                product_specs={"bundle": {"variant_id": bundle_variant_id}, "variants": [variant_id1, variant_id2]},
            )
        )
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user1.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user2.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user3.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user4.id, event_id=event.id, look_id=look1.id)
        )
        discount = self.app.discount_service.create_discount(
            event.id,
            attendee1.id,
            random.randint(50, 200),
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        response = self.client.open(
            f"/attendees/{str(attendee1.id)}/apply-discounts",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.apply_discounts_request(event_id=event.id).model_dump(), cls=encoder.CustomJSONEncoder
            ),
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assertTrue(
            (
                response.json[0] == discount.shopify_discount_code
                and response.json[1].startswith(TMG_GROUP_DISCOUNT_CODE_PREFIX)
            )
            or (
                response.json[1] == discount.shopify_discount_code
                and response.json[0].startswith(TMG_GROUP_DISCOUNT_CODE_PREFIX)
            )
        )

    def test_apply_discounts_with_full_pay_discounts(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs={"variants": [123, 234]})
        )
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )
        discount = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(50, 200),
            DiscountType.FULL_PAY,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        response = self.client.open(
            f"/attendees/{str(attendee.id)}/apply-discounts",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.apply_discounts_request(event_id=event.id).model_dump(), cls=encoder.CustomJSONEncoder
            ),
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0], discount.shopify_discount_code)

    def test_apply_discounts_with_full_pay_discounts_and_party_of_4(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        variant_id1 = 123
        variant_id2 = 234
        bundle_variant_id = variant_id1 + variant_id2
        look1 = self.look_service.create_look(
            fixtures.create_look_request(
                user_id=user.id,
                product_specs={"bundle": {"variant_id": bundle_variant_id}, "variants": [variant_id1, variant_id2]},
            )
        )
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user1.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user2.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user3.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user4.id, event_id=event.id, look_id=look1.id)
        )

        discount = self.app.discount_service.create_discount(
            event.id,
            attendee1.id,
            random.randint(50, 500),
            DiscountType.FULL_PAY,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        response = self.client.open(
            f"/attendees/{str(attendee1.id)}/apply-discounts",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.apply_discounts_request(event_id=event.id).model_dump(), cls=encoder.CustomJSONEncoder
            ),
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assertTrue(discount.shopify_discount_code in {response.json[0], response.json[1]})
        self.assertTrue(
            response.json[0].startswith(TMG_GROUP_DISCOUNT_CODE_PREFIX)
            or response.json[1].startswith(TMG_GROUP_DISCOUNT_CODE_PREFIX)
        )

    def test_apply_discounts_with_gift_discounts_and_party_of_4_when_tmg_discount_already_issued(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs={"variants": [123, 234]})
        )
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user1.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user2.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user3.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user4.id, event_id=event.id, look_id=look1.id)
        )
        discount1 = self.app.discount_service.create_discount(
            event.id,
            attendee1.id,
            random.randint(50, 200),
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        discount2 = self.app.discount_service.create_discount(
            event.id,
            attendee1.id,
            100,
            DiscountType.PARTY_OF_FOUR,
            False,
            f"{TMG_GROUP_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        # when
        response = self.client.open(
            f"/attendees/{str(attendee1.id)}/apply-discounts",
            query_string=self.hmac_query_params,
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(
                fixtures.apply_discounts_request(event_id=event.id).model_dump(), cls=encoder.CustomJSONEncoder
            ),
        )

        # then
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json), 2)
        self.assertEqual(set(response.json), {discount1.shopify_discount_code, discount2.shopify_discount_code})
