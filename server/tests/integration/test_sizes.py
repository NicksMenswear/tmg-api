import json

from server.tests.integration import BaseTestCase, fixtures


class TestSizes(BaseTestCase):
    def test_create_sizes(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        attendee1 = self.attendee_service.create_attendee(fixtures.create_attendee_request(user_id=user.id))
        attendee2 = self.attendee_service.create_attendee(fixtures.create_attendee_request(user_id=user.id))

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

        # Size was set for existing attendee
        attendee1 = self.attendee_service.get_attendee(attendee1.id)
        self.assertIsTrue(attendee1.size)
        attendee2 = self.attendee_service.get_attendee(attendee2.id)
        self.assertIsTrue(attendee2.size)

        # Size is set for every new attendee
        attendee3 = self.attendee_service.create_attendee(fixtures.create_attendee_request(user_id=user.id))
        self.assertIsTrue(attendee3.size)
        attendee3 = self.attendee_service.get_attendee(attendee3.id)
        self.assertIsTrue(attendee3.size)
