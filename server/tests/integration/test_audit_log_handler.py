from datetime import datetime

from sqlalchemy import select

from server.database.database_manager import db
from server.database.models import User, AuditLog, Event, Attendee
from server.handlers.audit_log_handler import (
    lambda_handler,
    TAG_EVENT_OWNER_4_PLUS,
    FakeLambdaContext,
    TAG_MEMBER_OF_4_PLUS_EVENT,
)
from server.services.integrations.shopify_service import ShopifyService
from server.tests.integration import BaseTestCase, fixtures


class TestAuditLogHandler(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_no_records(self):
        response = lambda_handler({}, FakeLambdaContext())
        self.assertEqual(response["statusCode"], 200)

    def test_single_item(self):
        # given
        user_model = self.user_service.create_user(fixtures.create_user_request())
        user = db.session.execute(select(User).where(User.id == user_model.id)).scalar_one()

        # when
        response = lambda_handler(
            {"Records": [{"body": fixtures.audit_log_queue_message("USER_CREATED", user)}]}, FakeLambdaContext()
        )

        # then
        audit_log_user = db.session.execute(select(AuditLog)).scalars().first()
        self.assertEqual(audit_log_user.type, "USER_CREATED")
        self.assertEqual(response["statusCode"], 200)

    def test_multiple_items(self):
        # given
        user_model1 = self.user_service.create_user(fixtures.create_user_request())
        user1 = db.session.execute(select(User).where(User.id == user_model1.id)).scalar_one()

        user_model2 = self.user_service.create_user(fixtures.create_user_request())
        user2 = db.session.execute(select(User).where(User.id == user_model2.id)).scalar_one()

        # when
        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("USER_CREATED", user1)},
                    {"body": fixtures.audit_log_queue_message("USER_UPDATED", user2)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()

        audit_log_user1 = audit_logs[0]
        audit_log_user2 = audit_logs[1]

        self.assertEqual({audit_log_user1.type, audit_log_user2.type}, {"USER_CREATED", "USER_UPDATED"})
        self.assertEqual(response["statusCode"], 200)

    def test_event_updated_user_is_not_owner_of_event_of_4(self):
        # given
        tags = ["test1", TAG_EVENT_OWNER_4_PLUS, "test2"]
        user_model = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags}))
        event_model = self.event_service.create_event(fixtures.create_event_request(user_id=user_model.id))
        event = db.session.execute(select(Event).where(Event.id == event_model.id)).scalar_one()

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = {
            "id": user_model.shopify_id,
            "tags": tags,
        }

        # when
        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("EVENT_UPDATED", event)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]

        self.assertTrue(
            TAG_EVENT_OWNER_4_PLUS
            not in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].get("tags", [])
        )
        self.assertTrue(
            TAG_EVENT_OWNER_4_PLUS not in db.session.execute(select(User)).scalars().first().meta.get("tags", [])
        )
        self.assertEqual(audit_log_event.type, "EVENT_UPDATED")
        self.assertEqual(response["statusCode"], 200)

    def test_event_updated_user_is_owner_of_event_of_4(self):
        # given
        tags = ["test1", TAG_EVENT_OWNER_4_PLUS, "test2"]
        user_model = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags}))
        event_model = self.event_service.create_event(fixtures.create_event_request(user_id=user_model.id))
        event = db.session.execute(select(Event).where(Event.id == event_model.id)).scalar_one()
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = {
            "id": user_model.shopify_id,
            "tags": tags,
        }

        # when
        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("EVENT_UPDATED", event)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]

        self.assertTrue(
            TAG_EVENT_OWNER_4_PLUS
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].get("tags", [])
        )
        self.assertTrue(
            TAG_EVENT_OWNER_4_PLUS in db.session.execute(select(User)).scalars().first().meta.get("tags", [])
        )
        self.assertEqual(audit_log_event.type, "EVENT_UPDATED")
        self.assertEqual(response["statusCode"], 200)

    def test_event_updated_user_is_owner_of_event_of_4_but_one_is_not_active(self):
        # given
        tags = ["test1", TAG_EVENT_OWNER_4_PLUS, "test2"]
        user_model = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags}))
        event_model = self.event_service.create_event(fixtures.create_event_request(user_id=user_model.id))
        event = db.session.execute(select(Event).where(Event.id == event_model.id)).scalar_one()
        attendee1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, invite=True)
        )
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))

        self.attendee_service.deactivate_attendee(attendee_id=attendee1.id)

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = {
            "id": user_model.shopify_id,
            "tags": tags,
        }

        # when
        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("EVENT_UPDATED", event)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]

        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].get("tags", [])
        )
        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS in db.session.execute(select(User)).scalars().first().meta.get("tags", [])
        )
        self.assertEqual(audit_log_event.type, "EVENT_UPDATED")
        self.assertEqual(response["statusCode"], 200)

    def test_event_updated_but_event_is_not_active(self):
        # given
        tags = ["test1", TAG_EVENT_OWNER_4_PLUS, "test2"]
        user_model = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags}))
        event_model = self.event_service.create_event(fixtures.create_event_request(user_id=user_model.id))
        event = db.session.execute(select(Event).where(Event.id == event_model.id)).scalar_one()
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))

        self.event_service.delete_event(event_id=event.id, force=True)

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = {
            "id": user_model.shopify_id,
            "tags": ["test1", TAG_EVENT_OWNER_4_PLUS, "test2"],
        }

        # when
        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("EVENT_UPDATED", event)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]

        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].get("tags", [])
        )
        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS in db.session.execute(select(User)).scalars().first().meta.get("tags", [])
        )
        self.assertEqual(audit_log_event.type, "EVENT_UPDATED")
        self.assertEqual(response["statusCode"], 200)

    def test_event_attendee_created_and_now_event_has_4_attendee(self):
        # given
        tags = ["test1", "test2"]
        user_model = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags}))
        event_model = self.event_service.create_event(fixtures.create_event_request(user_id=user_model.id))
        event = db.session.execute(select(Event).where(Event.id == event_model.id)).scalar_one()
        attendee_model1 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee_model2 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee_model3 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee_model4 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee4 = db.session.execute(select(Attendee).where(Attendee.id == attendee_model4.id)).scalar_one()
        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = {
            "id": user_model.shopify_id,
            "tags": tags,
        }
        self.attendee_service.send_invites(
            attendee_ids=[attendee_model1.id, attendee_model2.id, attendee_model3.id, attendee_model4.id]
        )

        for attendee in self.attendee_service.get_invited_attendees_for_the_event(event_id=event.id):
            attendee_user = self.user_service.get_user_by_id(attendee.user_id)
            self.shopify_service.customers[ShopifyService.customer_gid(attendee_user.shopify_id)] = {
                "id": attendee_user.shopify_id,
                "tags": {"test3"},
            }

        # when
        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("ATTENDEE_UPDATED", attendee4)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]

        self.assertTrue(
            TAG_EVENT_OWNER_4_PLUS
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].get("tags", [])
        )
        self.assertTrue(
            TAG_EVENT_OWNER_4_PLUS in db.session.execute(select(User)).scalars().first().meta.get("tags", [])
        )
        self.assertEqual(audit_log_event.type, "ATTENDEE_UPDATED")
        self.assertEqual(response["statusCode"], 200)

    def test_event_attendee_created_and_then_other_attendee_removed(self):
        # given
        tags = ["test1", "test2"]
        user_model = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags}))
        event_model = self.event_service.create_event(fixtures.create_event_request(user_id=user_model.id))
        event = db.session.execute(select(Event).where(Event.id == event_model.id)).scalar_one()

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = {
            "id": user_model.shopify_id,
            "tags": tags,
        }

        attendee_model1 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee_model2 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee_model3 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee_model4 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))

        attendee3 = db.session.execute(select(Attendee).where(Attendee.id == attendee_model3.id)).scalar_one()
        attendee4 = db.session.execute(select(Attendee).where(Attendee.id == attendee_model4.id)).scalar_one()

        self.attendee_service.send_invites(
            attendee_ids=[attendee_model1.id, attendee_model2.id, attendee_model3.id, attendee_model4.id]
        )

        for attendee in self.attendee_service.get_invited_attendees_for_the_event(event_id=event.id):
            attendee_user = self.user_service.get_user_by_id(attendee.user_id)
            self.shopify_service.customers[ShopifyService.customer_gid(attendee_user.shopify_id)] = {
                "id": attendee_user.shopify_id,
                "tags": {"test3"},
            }

        # when
        lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("ATTENDEE_UPDATED", attendee3)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        self.assertTrue(
            TAG_EVENT_OWNER_4_PLUS
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].get("tags", [])
        )

        # when
        self.attendee_service.deactivate_attendee(attendee_id=attendee4.id)

        lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("ATTENDEE_UPDATED", attendee4)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].get("tags", [])
        )
        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS in db.session.execute(select(User)).scalars().first().meta.get("tags", [])
        )

    def test_event_updated_user_is_owner_of_event_of_4_but_one_attendee_is_not_invited(self):
        # given
        tags = ["test1", TAG_EVENT_OWNER_4_PLUS, "test2"]
        user_model = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags}))
        event_model = self.event_service.create_event(fixtures.create_event_request(user_id=user_model.id))
        event = db.session.execute(select(Event).where(Event.id == event_model.id)).scalar_one()
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=False))

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = {
            "id": user_model.shopify_id,
            "tags": tags,
        }

        # when
        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("EVENT_UPDATED", event)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]

        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].get("tags", [])
        )
        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS in db.session.execute(select(User)).scalars().first().meta.get("tags", [])
        )
        self.assertEqual(audit_log_event.type, "EVENT_UPDATED")
        self.assertEqual(response["statusCode"], 200)

    def test_event_updated_user_is_owner_of_event_of_4_but_event_is_in_the_past(self):
        # given
        tags = ["test1", TAG_EVENT_OWNER_4_PLUS, "test2"]
        user_model = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags}))
        event_model = self.event_service.create_event(fixtures.create_event_request(user_id=user_model.id))
        event = db.session.execute(select(Event).where(Event.id == event_model.id)).scalar_one()
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))
        self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id, invite=True))

        event.event_at = datetime.now().replace(year=2020)
        db.session.commit()

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = {
            "id": user_model.shopify_id,
            "tags": tags,
        }

        # when
        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("EVENT_UPDATED", event)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]

        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].get("tags", [])
        )
        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS in db.session.execute(select(User)).scalars().first().meta.get("tags", [])
        )
        self.assertEqual(audit_log_event.type, "EVENT_UPDATED")
        self.assertEqual(response["statusCode"], 200)
