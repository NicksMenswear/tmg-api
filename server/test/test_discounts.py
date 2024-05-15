from __future__ import absolute_import

import json
import uuid

from server import encoder
from server.database.models import DiscountType
from server.services.attendee import AttendeeService
from server.services.discount import DiscountService
from server.services.event import EventService
from server.services.user import UserService
from server.test import BaseTestCase, fixtures


class TestDiscounts(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.user_service = UserService()
        self.event_service = EventService()
        self.attendee_service = AttendeeService()
        self.discount_service = DiscountService()

    def test_get_discounts_from_event_without_discounts(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))

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
        self.assert200(response)
        self.assertEqual(len(response.json), 0)

    def test_get_discounts(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user1 = self.user_service.create_user(fixtures.user_request())
        attendee_user2 = self.user_service.create_user(fixtures.user_request())
        attendee1 = self.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user1.id, event_id=event.id)
        )
        attendee2 = self.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user2.id, event_id=event.id)
        )
        intents = self.discount_service.create_groom_gift_discount_intents(
            event.id,
            [
                fixtures.create_discount_intent_request(attendee_id=attendee1.id),
                fixtures.create_discount_intent_request(attendee_id=attendee2.id),
            ],
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
        self.assertEqual(len(response.json), 2)

        if response.json[0]["attendee_id"] == str(intents[0].attendee_id):
            discount_intent1 = response.json[0]
            discount_intent2 = response.json[1]
        else:
            discount_intent1 = response.json[1]
            discount_intent2 = response.json[0]

        self.assertEqual(discount_intent1["attendee_id"], str(intents[0].attendee_id))
        self.assertEqual(discount_intent1["amount"], intents[0].amount)
        self.assertEqual(discount_intent2["attendee_id"], str(intents[1].attendee_id))
        self.assertEqual(discount_intent2["amount"], intents[1].amount)
        self.assertIsNotNone(discount_intent1["id"])
        self.assertEqual(discount_intent1["event_id"], str(event.id))
        self.assertIsNone(discount_intent1["code"])
        self.assertIsNotNone(discount_intent1["created_at"])
        self.assertIsNotNone(discount_intent1["updated_at"])

    def test_create_discount_intent_for_invalid_event(self):
        # when
        response = self.client.open(
            f"/events/{str(uuid.uuid4())}/discounts",
            query_string=self.hmac_query_params,
            method="POST",
            content_type=self.content_type,
            headers=self.request_headers,
            data=json.dumps([fixtures.create_discount_intent_request()], cls=encoder.CustomJSONEncoder),
        )

        # then
        self.assert404(response)

    def test_create_discount_intent_for_invalid_attendee(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.user_request())
        attendee = self.attendee_service.create_attendee(
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
                    fixtures.create_discount_intent_request(attendee_id=str(attendee.id)),
                    fixtures.create_discount_intent_request(attendee_id=str(uuid.uuid4())),
                ],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assert404(response)

    def test_create_discount_intent_with_invalid_amount(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.user_request())
        attendee = self.attendee_service.create_attendee(
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

    def test_create_discount_intents(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user1 = self.user_service.create_user(fixtures.user_request())
        attendee1 = self.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user1.id, event_id=event.id)
        )
        attendee_user2 = self.user_service.create_user(fixtures.user_request())
        attendee2 = self.attendee_service.create_attendee(
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
                [
                    create_discount_intent_request1,
                    create_discount_intent_request2,
                ],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(len(response.json), 2)

        discount_intent1 = response.json[0]
        self.assertEqual(discount_intent1["attendee_id"], str(attendee1.id))
        self.assertEqual(discount_intent1["amount"], create_discount_intent_request1["amount"])
        self.assertEqual(discount_intent1["type"], str(DiscountType.GROOM_GIFT))
        self.assertEqual(discount_intent1["event_id"], str(event.id))
        self.assertIsNotNone(discount_intent1["id"])
        self.assertIsNone(discount_intent1["code"])
        self.assertIsNotNone(discount_intent1["created_at"])
        self.assertIsNotNone(discount_intent1["updated_at"])

    def test_create_discount_intents_for_the_second_item_for_the_same_user(self):
        # given
        user = self.user_service.create_user(fixtures.user_request())
        event = self.event_service.create_event(fixtures.event_request(user_id=user.id))
        attendee_user1 = self.user_service.create_user(fixtures.user_request())
        attendee1 = self.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user1.id, event_id=event.id)
        )
        attendee_user2 = self.user_service.create_user(fixtures.user_request())
        attendee2 = self.attendee_service.create_attendee(
            fixtures.attendee_request(user_id=attendee_user2.id, event_id=event.id)
        )
        intents = self.discount_service.create_groom_gift_discount_intents(
            event.id,
            [
                fixtures.create_discount_intent_request(attendee_id=attendee1.id),
                fixtures.create_discount_intent_request(attendee_id=attendee2.id),
            ],
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
                [
                    create_discount_intent_request1,
                    create_discount_intent_request2,
                ],
                cls=encoder.CustomJSONEncoder,
            ),
        )

        # then
        self.assertStatus(response, 201)
        self.assertEqual(len(response.json), 2)

        discount_intent1 = response.json[0]
        self.assertEqual(discount_intent1["attendee_id"], str(attendee1.id))
        self.assertEqual(discount_intent1["amount"], create_discount_intent_request1["amount"])
        self.assertEqual(discount_intent1["event_id"], str(event.id))
        self.assertIsNotNone(discount_intent1["id"])
        self.assertIsNone(discount_intent1["code"])
        self.assertIsNotNone(discount_intent1["created_at"])
        self.assertIsNotNone(discount_intent1["updated_at"])
