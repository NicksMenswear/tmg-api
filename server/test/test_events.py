from __future__ import absolute_import

import uuid

from server.database.models import Event
from server.services.event import EventService
from server.services.user import UserService
from server.test import BaseTestCase
from server.test.fixtures import create_user_request_payload, create_event_request_payload


# - get non existing event by id           - 404
# - get existing event by id               - 200
# - create event with existing id          - 400
# - create event with all fields populated - 201
# - create event with missing fields       - 400
# - get list of events in empty db         - 200, []
# - get list of events in non empty db     - 200, [...]
# - update event with non existing id      - 404
# - update event with existing id          - 200
# - update event with missing fields       - 400
# - delete event with non existing id      - 404
# - delete event with existing id          - 204


class TestEvents(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.user_service = UserService(self.session_factory)
        self.event_service = EventService(self.session_factory)

    def assert_equal_response_event_with_db_event(self, event: Event, response_event: dict):
        self.assertEqual(response_event["id"], str(event.id))
        self.assertEqual(response_event["event_name"], event.event_name)
        self.assertEqual(response_event["event_date"], str(event.event_date))
        self.assertEqual(response_event["user_id"], str(event.user_id))
        self.assertEqual(response_event["is_active"], event.is_active)

        if len(response_event["looks"]) > 0:
            pass

    def test_get_events_for_non_existing_user_by_email(self):
        # when
        response = self.client.open(
            "/events/{email}".format(email=f"{str(uuid.uuid4())}@example.com"),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
        )

        # then
        self.assert404(response)

    def test_get_empty_list_of_events_by_user_email(self):
        # given
        email = f"{str(uuid.uuid4())}@example.com"
        self.user_service.create_user(**create_user_request_payload(email=email))

        # when
        response = self.client.open(
            "/events/{email}".format(email=email),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(response.json, [])

    def test_get_list_of_2_events_by_user_email_but_only_1_active(self):
        # given
        email = f"{str(uuid.uuid4())}@example.com"
        user = self.user_service.create_user(**create_user_request_payload(email=email))

        self.event_service.create_event(**create_event_request_payload(user_id=user.id, is_active=False))
        active_event = self.event_service.create_event(**create_event_request_payload(user_id=user.id, is_active=True))

        # when
        response = self.client.open(
            "/events/{email}".format(email=email),
            query_string=self.hmac_query_params,
            method="GET",
            content_type=self.content_type,
        )

        # then
        self.assert200(response)
        self.assertEqual(len(response.json), 1)
        self.assert_equal_response_event_with_db_event(active_event, response.json[0])
