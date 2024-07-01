import json

from server.tests.integration import BaseTestCase, fixtures


class TestSizes(BaseTestCase):
    def test_create_size(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())

        # when
        response = self.client.open(
            "/sizes",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(fixtures.store_size_request(user_id=str(user.id))),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])

    def test_create_size_with_existing_attendees(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        user = self.user_service.create_user(fixtures.create_user_request())
        event1 = self.event_service.create_event(fixtures.create_event_request(user_id=str(owner.id)))
        event2 = self.event_service.create_event(fixtures.create_event_request(user_id=str(owner.id)))
        attendee1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=user.email, event_id=str(event1.id))
        )
        attendee2 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=user.email, event_id=str(event2.id))
        )

        # when
        response = self.client.open(
            "/sizes",
            method="POST",
            headers=self.request_headers,
            content_type=self.content_type,
            data=json.dumps(fixtures.store_size_request(user_id=str(user.id))),
        )

        # then
        self.assertStatus(response, 201)
        self.assertIsNotNone(response.json["id"])

        # Size was set for existing attendees
        attendee1 = self.attendee_service.get_attendee_by_id(attendee1.id)
        self.assertTrue(attendee1.size)
        attendee2 = self.attendee_service.get_attendee_by_id(attendee2.id)
        self.assertTrue(attendee2.size)

    def test_create_size_and_new_attendee(self):
        # given
        owner = self.user_service.create_user(fixtures.create_user_request())
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=str(owner.id)))
        self.size_service.create_size(fixtures.store_size_request(user_id=str(user.id)))

        # when
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(email=user.email, event_id=str(event.id))
        )

        # then
        # Size is set for every new attendee
        self.assertTrue(attendee.size)
        attendee = self.attendee_service.get_attendee_by_id(attendee.id)
        self.assertTrue(attendee.size)
