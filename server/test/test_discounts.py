from __future__ import absolute_import

import json
import uuid

from server import encoder
from server.database.models import DiscountType
from server.test import BaseTestCase, fixtures


class TestDiscounts(BaseTestCase):
    def test_get_discounts_for_invalid_event(self):
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

    def test_get_groom_gift_discounts_from_event_without_attendees(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))

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

    def test_get_groom_gift_discounts_from_event_with_attendees_and_looks_but_without_any_discounts(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.user_request())
        attendee_user2 = self.app.user_service.create_user(fixtures.user_request())
        look1 = self.app.look_service.create_look(
            fixtures.look_request(user_id=attendee_user1.id, product_specs={"variants": [1234, 5678, 1715]})
        )
        look2 = self.app.look_service.create_look(
            fixtures.look_request(user_id=attendee_user2.id, product_specs={"variants": [9988, 1715]})
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(email=attendee_user1.email, event_id=event.id, look_id=look1.id)
        )
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(email=attendee_user2.email, event_id=event.id, look_id=look2.id)
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
        self.assertEqual(discount_item1["amount"], 0)
        self.assertEqual(len(discount_item1["codes"]), 0)
        self.assertEqual(discount_item1["look"]["id"], str(attendee1["look"].id))
        self.assertEqual(discount_item1["look"]["name"], attendee1["look"].look_name)
        self.assertEqual(len(discount_item1["codes"]), 0)

        self.assertEqual(discount_item2["attendee_id"], str(attendee2["attendee"].id))
        self.assertEqual(discount_item2["first_name"], attendee2["user"].first_name)
        self.assertEqual(discount_item2["last_name"], attendee2["user"].last_name)
        self.assertEqual(discount_item2["event_id"], str(event.id))
        self.assertEqual(discount_item2["amount"], 0)
        self.assertEqual(len(discount_item2["codes"]), 0)
        self.assertEqual(discount_item2["look"]["id"], str(attendee2["look"].id))
        self.assertEqual(discount_item2["look"]["name"], attendee2["look"].look_name)
        self.assertEqual(len(discount_item2["codes"]), 0)

    # def test_get_discounts(self):
    #     # given
    #     user = self.app.user_service.create_user(fixtures.user_request())
    #     event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
    #     attendee_user1 = self.app.user_service.create_user(fixtures.user_request())
    #     attendee_user2 = self.app.user_service.create_user(fixtures.user_request())
    #     attendee1 = self.app.attendee_service.create_attendee(
    #         fixtures.attendee_request(user_id=attendee_user1.id, event_id=event.id)
    #     )
    #     attendee2 = self.app.attendee_service.create_attendee(
    #         fixtures.attendee_request(user_id=attendee_user2.id, event_id=event.id)
    #     )
    #     intents = self.app.discount_service.create_groom_gift_discount_intents(
    #         event.id,
    #         [
    #             fixtures.create_discount_intent_request(attendee_id=attendee1.id),
    #             fixtures.create_discount_intent_request(attendee_id=attendee2.id),
    #         ],
    #     )
    #
    #     # when
    #     response = self.client.open(
    #         f"/events/{event.id}/discounts",
    #         query_string=self.hmac_query_params,
    #         method="GET",
    #         content_type=self.content_type,
    #         headers=self.request_headers,
    #     )
    #
    #     # then
    #     self.assert200(response)
    #     self.assertEqual(len(response.json), 2)
    #
    #     if response.json[0]["attendee_id"] == str(intents[0].attendee_id):
    #         discount_intent1 = response.json[0]
    #         discount_intent2 = response.json[1]
    #     else:
    #         discount_intent1 = response.json[1]
    #         discount_intent2 = response.json[0]
    #
    #     self.assertEqual(discount_intent1["attendee_id"], str(intents[0].attendee_id))
    #     self.assertEqual(discount_intent1["amount"], intents[0].amount)
    #     self.assertEqual(discount_intent2["attendee_id"], str(intents[1].attendee_id))
    #     self.assertEqual(discount_intent2["amount"], intents[1].amount)
    #     self.assertIsNotNone(discount_intent1["id"])
    #     self.assertEqual(discount_intent1["event_id"], str(event.id))
    #     self.assertIsNone(discount_intent1["code"])
    #     self.assertIsNotNone(discount_intent1["created_at"])
    #     self.assertIsNotNone(discount_intent1["updated_at"])
    #
    # def test_create_discount_intent_for_invalid_event(self):
    #     # when
    #     response = self.client.open(
    #         f"/events/{str(uuid.uuid4())}/discounts",
    #         query_string=self.hmac_query_params,
    #         method="POST",
    #         content_type=self.content_type,
    #         headers=self.request_headers,
    #         data=json.dumps([fixtures.create_discount_intent_request()], cls=encoder.CustomJSONEncoder),
    #     )
    #
    #     # then
    #     self.assert404(response)

    def test_create_discount_intent_for_invalid_event(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user.id, event_id=event.id)
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
                    fixtures.create_discount_intent_request(attendee_id=str(attendee.id)),
                ],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert404(response)

    def test_create_discount_intent_with_empty_intents_input(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))

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
        self.assertStatus(response, 201)
        self.assertEqual(len(response.json), 0)

    def test_create_discount_intent_for_invalid_one_attendee(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user.id, event_id=event.id)
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
                    fixtures.create_discount_intent_request(attendee_id=str(attendee.id)),  # valid attendee_id
                    fixtures.create_discount_intent_request(attendee_id=str(uuid.uuid4())),  # invalid attendee_id
                ],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert404(response)

    def test_create_discount_intent_for_not_active_attendee(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user.id, event_id=event.id, is_active=False)
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
                    fixtures.create_discount_intent_request(attendee_id=str(attendee.id)),
                ],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert404(response)

    def test_create_discount_intent_both_amount_and_pay_full_missing(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user.id, event_id=event.id)
        )
        discount_intent_request = fixtures.create_discount_intent_request(attendee_id=str(attendee.id))
        del discount_intent_request["amount"]
        del discount_intent_request["pay_full"]

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

    def test_create_discount_intent_both_amount_is_required_if_pay_full_is_false(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user.id, event_id=event.id)
        )
        discount_intent_request = fixtures.create_discount_intent_request(attendee_id=str(attendee.id), pay_full=False)
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

    def test_create_discount_intent_both_amount_and_pay_full_present(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user.id, event_id=event.id)
        )
        discount_intent_request = fixtures.create_discount_intent_request(attendee_id=str(attendee.id), pay_full=True)

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
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user.id, event_id=event.id)
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
                    fixtures.create_discount_intent_request(attendee_id=str(attendee.id), amount=-100),
                ],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert400(response)

    def test_create_discount_intent_of_type_groom_gift(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user.id, event_id=event.id)
        )

        # when
        create_discount_intent_request = fixtures.create_discount_intent_request(attendee_id=str(attendee.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [create_discount_intent_request],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(len(response.json), 1)

        discount_intent = response.json[0]
        self.assertEqual(discount_intent["attendee_id"], str(attendee.id))
        self.assertEqual(discount_intent["amount"], create_discount_intent_request["amount"])
        self.assertEqual(discount_intent["type"], str(DiscountType.GROOM_GIFT))
        self.assertEqual(discount_intent["event_id"], str(event.id))
        self.assertIsNotNone(discount_intent["id"])
        self.assertIsNotNone(discount_intent["shopify_virtual_product_id"])
        self.assertIsNone(discount_intent["code"])
        self.assertFalse(discount_intent["used"])
        self.assertIsNotNone(discount_intent["created_at"])
        self.assertIsNotNone(discount_intent["updated_at"])

        shopify_virtual_product = self.app.shopify_service.shopify_virtual_products.get(
            int(discount_intent["shopify_virtual_product_id"])
        )
        self.assertIsNotNone(shopify_virtual_product)
        self.assertEqual(shopify_virtual_product["variants"][0]["price"], create_discount_intent_request["amount"])

    def test_create_discount_intent_of_type_groom_gift_for_2_attendees(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user1.id, event_id=event.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user2.id, event_id=event.id)
        )

        # when
        create_discount_intent_request1 = fixtures.create_discount_intent_request(attendee_id=str(attendee1.id))
        create_discount_intent_request2 = fixtures.create_discount_intent_request(attendee_id=str(attendee2.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [create_discount_intent_request1, create_discount_intent_request2],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(len(response.json), 2)

        discount_intent1 = response.json[0]
        discount_intent2 = response.json[1]

        self.assertEqual(
            discount_intent1["amount"] + discount_intent2["amount"],
            create_discount_intent_request1["amount"] + create_discount_intent_request2["amount"],
        )
        self.assertEqual(discount_intent1["type"], str(DiscountType.GROOM_GIFT))
        self.assertEqual(discount_intent1["event_id"], str(event.id))

    def test_create_discount_intent_of_type_groom_full_pay_look_not_set_for_attendee(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user.id, event_id=event.id)
        )

        # when
        create_discount_intent_request = fixtures.create_discount_intent_request(
            attendee_id=str(attendee.id), pay_full=True
        )
        del create_discount_intent_request["amount"]

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [create_discount_intent_request],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert404(response)

    def test_create_discount_intent_of_type_groom_full_pay_look_has_no_variants(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.user_request())
        look = self.app.look_service.create_look(fixtures.look_request(user_id=attendee_user.id))
        attendee = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )

        # when
        create_discount_intent_request = fixtures.create_discount_intent_request(
            attendee_id=str(attendee.id), pay_full=True
        )
        del create_discount_intent_request["amount"]

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [create_discount_intent_request],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 400)

    def test_create_discount_intent_of_type_groom_full_pay(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.user_request())
        look = self.app.look_service.create_look(
            fixtures.look_request(user_id=attendee_user.id, product_specs={"variants": [123, 234, 567]})
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user.id, event_id=event.id, look_id=look.id)
        )

        # when
        create_discount_intent_request = fixtures.create_discount_intent_request(
            attendee_id=str(attendee.id), pay_full=True
        )
        del create_discount_intent_request["amount"]

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [create_discount_intent_request],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(len(response.json), 1)

        discount_intent = response.json[0]
        self.assertEqual(discount_intent["attendee_id"], str(attendee.id))
        self.assertEqual(discount_intent["type"], str(DiscountType.GROOM_FULL_PAY))
        self.assertEqual(discount_intent["event_id"], str(event.id))
        self.assertEqual(discount_intent["amount"], (123 + 234 + 567) * 10)
        self.assertIsNotNone(discount_intent["id"])
        self.assertIsNone(discount_intent["code"])
        self.assertFalse(discount_intent["used"])
        self.assertIsNotNone(discount_intent["created_at"])
        self.assertIsNotNone(discount_intent["updated_at"])

    def test_create_discount_intent_of_mixed_types(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.user_request())
        look1 = self.app.look_service.create_look(
            fixtures.look_request(user_id=attendee_user1.id, product_specs={"variants": [123, 234]})
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user1.id, event_id=event.id, look_id=look1.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user2.id, event_id=event.id)
        )

        # when
        create_discount_intent_request1 = fixtures.create_discount_intent_request(
            attendee_id=str(attendee1.id), pay_full=True
        )
        del create_discount_intent_request1["amount"]
        create_discount_intent_request2 = fixtures.create_discount_intent_request(attendee_id=str(attendee2.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [create_discount_intent_request1, create_discount_intent_request2],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(len(response.json), 2)

        discount_intent1 = response.json[0]
        discount_intent2 = response.json[1]
        self.assertNotEqual(discount_intent1["type"], discount_intent2["type"])
        self.assertEqual(
            discount_intent1["type"] in [str(DiscountType.GROOM_FULL_PAY), str(DiscountType.GROOM_GIFT)], True
        )
        self.assertEqual(
            discount_intent2["type"] in [str(DiscountType.GROOM_FULL_PAY), str(DiscountType.GROOM_GIFT)], True
        )
        self.assertNotEqual(discount_intent1["amount"], discount_intent2["amount"])
        self.assertEqual(
            discount_intent1["amount"] in [123 * 10 + 234 * 10, create_discount_intent_request2.get("amount")], True
        )
        self.assertEqual(
            discount_intent2["amount"] in [123 * 10 + 234 * 10, create_discount_intent_request2.get("amount")], True
        )

    def test_create_discount_intent_for_party_of_4_of_type_groom_gift_but_only_one_attendee_has_intents_set(self):
        # given
        user = self.app.user_service.create_user(fixtures.user_request())
        event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user1.id, event_id=event.id)
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user2.id, event_id=event.id)
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user3.id, event_id=event.id)
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user4.id, event_id=event.id)
        )

        # when
        create_discount_intent_request = fixtures.create_discount_intent_request(attendee_id=str(attendee1.id))

        response = self.client.open(
            f"/events/{str(event.id)}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps(
                [create_discount_intent_request],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(len(response.json), 1)

        discount_intent = response.json[0]

    # def test_create_discount_intents_for_the_second_item_for_the_same_user(self):
    #     # given
    #     user = self.app.user_service.create_user(fixtures.user_request())
    #     event = self.app.event_service.create_event(fixtures.event_request(user_id=user.id))
    #     attendee_user1 = self.app.user_service.create_user(fixtures.user_request())
    #     attendee1 = self.app.attendee_service.create_attendee(
    #         fixtures.attendee_request(user_id=attendee_user1.id, event_id=event.id)
    #     )
    #     attendee_user2 = self.app.user_service.create_user(fixtures.user_request())
    #     attendee2 = self.app.attendee_service.create_attendee(
    #         fixtures.attendee_request(user_id=attendee_user2.id, event_id=event.id)
    #     )
    #     intents = self.app.discount_service.create_groom_gift_discount_intents(
    #         event.id,
    #         [
    #             fixtures.create_discount_intent_request(attendee_id=attendee1.id),
    #             fixtures.create_discount_intent_request(attendee_id=attendee2.id),
    #         ],
    #     )
    #
    #     # when
    #     create_discount_intent_request1 = fixtures.create_discount_intent_request(attendee_id=str(attendee1.id))
    #     create_discount_intent_request2 = fixtures.create_discount_intent_request(attendee_id=str(attendee2.id))
    #
    #     response = self.client.open(
    #         f"/events/{str(event.id)}/discounts",
    #         query_string=self.hmac_query_params,
    #         method="POST",
    #         content_type=self.content_type,
    #         headers=self.request_headers,
    #         data=json.dumps(
    #             [
    #                 create_discount_intent_request1,
    #                 create_discount_intent_request2,
    #             ],
    #             cls=encoder.CustomJSONEncoder,
    #         ),
    #     )
    #
    #     # then
    #     self.assertStatus(response, 201)
    #     self.assertEqual(len(response.json), 2)
    #
    #     discount_intent1 = response.json[0]
    #     self.assertEqual(discount_intent1["attendee_id"], str(attendee1.id))
    #     self.assertEqual(discount_intent1["amount"], create_discount_intent_request1["amount"])
    #     self.assertEqual(discount_intent1["event_id"], str(event.id))
    #     self.assertIsNotNone(discount_intent1["id"])
    #     self.assertIsNone(discount_intent1["code"])
    #     self.assertIsNotNone(discount_intent1["created_at"])
    #     self.assertIsNotNone(discount_intent1["updated_at"])
