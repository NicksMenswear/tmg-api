from __future__ import absolute_import

import json
import random
import uuid

from server import encoder
from server.database.models import DiscountType
from server.services.discount_service import (
    GIFT_DISCOUNT_CODE_PREFIX,
    TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX,
    TMG_GROUP_25_PERCENT_OFF_DISCOUNT_CODE_PREFIX,
)
from server.tests.integration import BaseTestCase, fixtures


class TestDiscountsApplyDiscounts(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.populate_shopify_variants()

    def test_apply_invalid_attendee(self):
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

    def test_apply_no_gift_discounts_exists(self):
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

    def test_apply_event_of_4_but_one_not_styled(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user1.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user2.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user3.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(user_id=attendee_user4.id, event_id=event.id, look_id=look.id, invite=True)
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
        self.assertEqual(len(response.json), 0)

    def test_apply_event_of_4_and_all_styled_and_invited(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        # hack to reduce price of the look so smaller discount is applied
        self.shopify_service.shopify_variants.get(
            look.product_specs["bundle"]["variant_id"]
        ).variant_price = random.randint(200, 299)
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user1.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user2.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user3.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user4.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
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
        self.assertTrue(response.json[0].startswith(TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX))

    def test_apply_with_gift_discounts(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee_user = self.app.user_service.create_user(fixtures.create_user_request())
        attendee = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
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

    def test_apply_with_gift_discounts_and_party_of_4_tmg_group_discount_50_usd(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        # hack to reduce price of the look so smaller discount is applied
        self.shopify_service.shopify_variants.get(
            look1.product_specs["bundle"]["variant_id"]
        ).variant_price = random.randint(200, 299)
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user1.id, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user2.id, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user3.id, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user4.id, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        discount = self.app.discount_service.create_discount(
            event.id,
            attendee1.id,
            random.randint(10, 15),
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
                and response.json[1].startswith(TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX)
            )
            or (
                response.json[1] == discount.shopify_discount_code
                and response.json[0].startswith(TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX)
            )
        )

    def test_apply_with_gift_discounts_and_party_of_4_tmg_group_discount_25_percent(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look1 = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user1.id, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user2.id, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user3.id, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user4.id, event_id=event.id, look_id=look1.id, invite=True, style=True
            )
        )
        discount = self.app.discount_service.create_discount(
            event.id,
            attendee1.id,
            random.randint(10, 15),
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
                and response.json[1].startswith(TMG_GROUP_25_PERCENT_OFF_DISCOUNT_CODE_PREFIX)
            )
            or (
                response.json[1] == discount.shopify_discount_code
                and response.json[0].startswith(TMG_GROUP_25_PERCENT_OFF_DISCOUNT_CODE_PREFIX)
            )
        )

    def test_apply_with_gift_discounts_and_party_of_4_when_tmg_discount_already_issued(self):
        user = self.app.user_service.create_user(fixtures.create_user_request())
        event = self.app.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        look = self.look_service.create_look(
            fixtures.create_look_request(user_id=user.id, product_specs=self.create_look_test_product_specs())
        )
        attendee_user1 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user1.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        attendee_user2 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee2 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user2.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        attendee_user3 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee3 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user3.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
        )
        attendee_user4 = self.app.user_service.create_user(fixtures.create_user_request())
        attendee4 = self.app.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                user_id=attendee_user4.id, event_id=event.id, look_id=look.id, invite=True, style=True
            )
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
            f"{TMG_GROUP_50_USD_OFF_DISCOUNT_CODE_PREFIX}-{random.randint(100000, 1000000)}",
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
