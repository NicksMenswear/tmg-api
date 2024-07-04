from __future__ import absolute_import

import random
import uuid

from server.database.models import DiscountType
from server.services.discount import (
    GIFT_DISCOUNT_CODE_PREFIX,
    TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX,
    TMG_GROUP_25_PERCENT_OFF_DISCOUNT_CODE_PREFIX,
    TMG_GROUP_50_USD_AMOUNT,
    TMG_GROUP_25_PERCENT_OFF,
)
from server.tests.integration import BaseTestCase, fixtures


class TestDiscountsGetOwnerDiscounts(BaseTestCase):
    def test_get_for_invalid_event(self):
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

    def test_get_from_event_without_attendees(self):
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

    def test_get_from_event_with_attendees_and_looks_but_without_any_discounts(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        look1 = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user1.id, product_specs={"bundle": {"variant_id": 124}})
        )
        look2 = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user2.id, product_specs={"bundle": {"variant_id": 829}})
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user1.email, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user2.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
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

    def test_get_with_2_gift_codes_gift_one_paid_and_one_not_paid(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user.id, product_specs={"variants": [1234, 5678, 1715]})
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user.email, event_id=event.id, look_id=look.id, invite=True, style=True
            )
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

    def test_get_no_tmg_group_discount_for_event_with_less_then_4_attendees(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        look1 = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user1.id, product_specs={"bundle": {"variant_id": 26}})
        )
        look2 = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user2.id, product_specs={"bundle": {"variant_id": 31}})
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user1.email, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user2.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user3.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
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
        self.assertEqual(len(response.json), 3)

        for discount in response.json:
            self.assertTrue(len(discount["gift_codes"]) == 0)

    def test_get_no_tmg_group_discount_for_event_with_4_attendees_but_one_is_not_styled(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        look1 = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user1.id, product_specs={"bundle": {"variant_id": 26}})
        )
        look2 = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user2.id, product_specs={"bundle": {"variant_id": 31}})
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user1.email, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user2.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user3.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user4.email, event_id=event.id, look_id=None, invite=True, style=False
            )
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
        self.assertEqual(len(response.json), 4)

        for discount in response.json:
            self.assertTrue(len(discount["gift_codes"]) == 0)

    def test_get_no_tmg_group_discount_for_event_with_4_attendees_but_one_is_not_invited(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        look1 = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user1.id, product_specs={"bundle": {"variant_id": 26}})
        )
        look2 = self.app.look_service.create_look(
            fixtures.create_look_request(user_id=attendee_user2.id, product_specs={"bundle": {"variant_id": 31}})
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user1.email, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user2.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user3.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user4.email, event_id=event.id, look_id=None, invite=False, style=True
            )
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
        self.assertEqual(len(response.json), 4)

        for discount in response.json:
            self.assertTrue(len(discount["gift_codes"]) == 0)

    def test_get_tmg_group_discounts_from_event_with_4_attendees(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        look1 = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user1.id, product_specs={"bundle": {"variant_id": random.randint(26, 29)}}
            )
        )
        look2 = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user2.id, product_specs={"bundle": {"variant_id": random.randint(31, 60)}}
            )
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user1.email, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user2.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user3.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user4.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
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
        self.assertEqual(len(response.json), 4)

        for discount in response.json:
            discount_attendee_id = discount["attendee_id"]

            if str(discount_attendee_id) == str(attendee1.id):
                self.assertEqual(discount["gift_codes"][0]["code"], TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX)
                self.assertEqual(discount["gift_codes"][0]["amount"], TMG_GROUP_50_USD_AMOUNT)
            else:
                look_price = self.look_service.get_look_price(look2)

                self.assertEqual(discount["gift_codes"][0]["code"], TMG_GROUP_25_PERCENT_OFF_DISCOUNT_CODE_PREFIX)
                self.assertEqual(discount["gift_codes"][0]["amount"], look_price * TMG_GROUP_25_PERCENT_OFF)

    def test_get_remaining_amount_for_attendee_without_look(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=attendee_user.email, event_id=event.id)
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
        self.assertEqual(response.json[0]["remaining_amount"], 0)

    def test_get_remaining_amount_for_attendee_not_invited(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id, product_specs={"bundle": {"variant_id": random.randint(26, 29)}}
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user.email, event_id=event.id, look_id=look.id, invite=False, style=True
            )
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
        self.assertEqual(response.json[0]["remaining_amount"], 0)

    def test_get_remaining_amount_for_attendee_not_styled(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id, product_specs={"bundle": {"variant_id": random.randint(26, 29)}}
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user.email, event_id=event.id, look_id=look.id, invite=True, style=False
            )
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
        self.assertEqual(response.json[0]["remaining_amount"], 0)

    def test_get_remaining_amount_for_attendee_whole_look_price(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id, product_specs={"bundle": {"variant_id": random.randint(26, 29)}}
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user.email, event_id=event.id, look_id=look.id, invite=True, style=True
            )
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
        self.assertEqual(response.json[0]["remaining_amount"], self.look_service.get_look_price(look))

    def test_get_remaining_amount_for_attendee_with_already_partially_paid_gift_code(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id, product_specs={"bundle": {"variant_id": random.randint(26, 29)}}
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user.email, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        discount = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(10, 90),
            DiscountType.GIFT,
            False,
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
        self.assertEqual(response.json[0]["remaining_amount"], self.look_service.get_look_price(look) - discount.amount)

    def test_get_remaining_amount_for_attendee_with_multiple_already_partially_paid_gift_code(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        look = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user.id, product_specs={"bundle": {"variant_id": random.randint(26, 29)}}
            )
        )
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user.email, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        discount1 = self.app.discount_service.create_discount(
            event.id,
            attendee.id,
            random.randint(10, 90),
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
            random.randint(10, 90),
            DiscountType.GIFT,
            False,
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
        self.assertEqual(
            response.json[0]["remaining_amount"],
            self.look_service.get_look_price(look) - discount1.amount - discount2.amount,
        )

    def test_get_remaining_amount_for_group_of_4(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        look1 = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user1.id, product_specs={"bundle": {"variant_id": random.randint(26, 29)}}
            )
        )
        look2 = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user2.id, product_specs={"bundle": {"variant_id": random.randint(31, 60)}}
            )
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user1.email, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user2.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user3.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user4.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
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
        self.assertEqual(len(response.json), 4)

        for discount in response.json:
            discount_attendee_id = discount["attendee_id"]

            if str(discount_attendee_id) == str(attendee1.id):
                look_price = self.look_service.get_look_price(look1)

                self.assertEqual(discount["remaining_amount"], look_price - TMG_GROUP_50_USD_AMOUNT)
            else:
                look_price = self.look_service.get_look_price(look2)

                self.assertEqual(discount["remaining_amount"], look_price - look_price * TMG_GROUP_25_PERCENT_OFF)

    def test_get_remaining_amount_for_group_of_4_with_discounts(self):
        # given
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        look1 = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user1.id, product_specs={"bundle": {"variant_id": random.randint(26, 29)}}
            )
        )
        look2 = self.app.look_service.create_look(
            fixtures.create_look_request(
                user_id=attendee_user2.id, product_specs={"bundle": {"variant_id": random.randint(31, 60)}}
            )
        )
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user1.email, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user2.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user3.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                email=attendee_user4.email, event_id=event.id, look_id=look2.id, invite=True, style=True
            )
        )
        discount1 = self.app.discount_service.create_discount(
            event.id,
            attendee1.id,
            random.randint(10, 90),
            DiscountType.GIFT,
            False,
            f"{GIFT_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
            random.randint(10000, 100000),
            random.randint(10000, 100000),
            random.randint(10000, 100000),
        )

        discount2 = self.app.discount_service.create_discount(
            event.id,
            attendee2.id,
            random.randint(10, 90),
            DiscountType.GIFT,
            False,
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
        self.assertEqual(len(response.json), 4)

        for discount in response.json:
            discount_attendee_id = discount["attendee_id"]

            if str(discount_attendee_id) == str(attendee1.id):
                look_price = self.look_service.get_look_price(look1)

                self.assertEqual(
                    discount["remaining_amount"],
                    look_price - discount1.amount - TMG_GROUP_50_USD_AMOUNT,
                )
            elif str(discount_attendee_id) == str(attendee2.id):
                look_price = self.look_service.get_look_price(look2)

                self.assertEqual(
                    discount["remaining_amount"], look_price - discount2.amount - look_price * TMG_GROUP_25_PERCENT_OFF
                )
