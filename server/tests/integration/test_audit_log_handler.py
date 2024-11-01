from datetime import datetime

from sqlalchemy import select

from server.database.database_manager import db
from server.database.models import User, AuditLog, Event, Attendee
from server.handlers.audit_log_handler import lambda_handler, FakeLambdaContext
from server.models.attendee_model import UpdateAttendeeModel
from server.models.shopify_model import ShopifyCustomer
from server.services.integrations.shopify_service import ShopifyService
from server.services.tagging_service import (
    TAG_EVENT_OWNER_4_PLUS,
    TAG_MEMBER_OF_4_PLUS_EVENT,
    TAG_PRODUCT_NOT_LINKED_TO_EVENT,
    TAG_PRODUCT_LINKED_TO_EVENT,
)
from server.tests import utils
from server.tests.integration import BaseTestCase, fixtures


class TestAuditLogHandler(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.populate_shopify_variants()

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

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = ShopifyCustomer(
            gid=ShopifyService.customer_gid(user_model.shopify_id),
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            email=user_model.email,
            tags=tags,
        )

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
            not in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].tags
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

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = ShopifyCustomer(
            gid=ShopifyService.customer_gid(user_model.shopify_id),
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            email=user_model.email,
            tags=tags,
        )

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
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].tags
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

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = ShopifyCustomer(
            gid=ShopifyService.customer_gid(user_model.shopify_id),
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            email=user_model.email,
            tags=["test1", TAG_EVENT_OWNER_4_PLUS, "test2"],
        )

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
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].tags
        )
        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS in db.session.execute(select(User)).scalars().first().meta.get("tags", [])
        )
        self.assertEqual(audit_log_event.type, "EVENT_UPDATED")
        self.assertEqual(response["statusCode"], 200)

    def test_attendee_created_and_now_event_has_4_attendee(self):
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
        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = ShopifyCustomer(
            gid=ShopifyService.customer_gid(user_model.shopify_id),
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            email=user_model.email,
            tags=tags,
        )
        self.attendee_service.send_invites(
            attendee_ids=[attendee_model1.id, attendee_model2.id, attendee_model3.id, attendee_model4.id]
        )

        for attendee in self.attendee_service.get_invited_attendees_for_the_event(event_id=event.id):
            attendee_user = self.user_service.get_user_by_id(attendee.user_id)
            self.shopify_service.customers[ShopifyService.customer_gid(attendee_user.shopify_id)] = ShopifyCustomer(
                gid=ShopifyService.customer_gid(attendee_user.shopify_id),
                first_name=attendee_user.first_name,
                last_name=attendee_user.last_name,
                email=attendee_user.email,
                tags=["test3"],
            )

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
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].tags
        )

        self.assertTrue(
            TAG_EVENT_OWNER_4_PLUS
            in db.session.execute(select(User).where(User.id == user_model.id)).scalars().first().meta.get("tags", [])
        )
        self.assertEqual(audit_log_event.type, "ATTENDEE_UPDATED")
        self.assertEqual(response["statusCode"], 200)

    def test_attendee_created_and_then_other_attendee_removed(self):
        # given
        tags = ["test1", "test2"]
        user_model = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags}))
        event_model = self.event_service.create_event(fixtures.create_event_request(user_id=user_model.id))
        event = db.session.execute(select(Event).where(Event.id == event_model.id)).scalar_one()

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = ShopifyCustomer(
            gid=ShopifyService.customer_gid(user_model.shopify_id),
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            email=user_model.email,
            tags=tags,
        )

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
            self.shopify_service.customers[ShopifyService.customer_gid(attendee_user.shopify_id)] = ShopifyCustomer(
                gid=ShopifyService.customer_gid(attendee_user.shopify_id),
                first_name=attendee_user.first_name,
                last_name=attendee_user.last_name,
                email=attendee_user.email,
                tags=["test3"],
            )

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
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].tags
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
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].tags
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

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = ShopifyCustomer(
            gid=ShopifyService.customer_gid(user_model.shopify_id),
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            email=user_model.email,
            tags=tags,
        )

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
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].tags
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

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = ShopifyCustomer(
            gid=ShopifyService.customer_gid(user_model.shopify_id),
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            email=user_model.email,
            tags=tags,
        )

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
            in self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)].tags
        )
        self.assertFalse(
            TAG_EVENT_OWNER_4_PLUS in db.session.execute(select(User)).scalars().first().meta.get("tags", [])
        )
        self.assertEqual(audit_log_event.type, "EVENT_UPDATED")
        self.assertEqual(response["statusCode"], 200)

    def test_attendee_removed(self):
        # given
        tags = ["test1"]
        user_model = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags}))
        event_model = self.event_service.create_event(fixtures.create_event_request(user_id=user_model.id))
        event = db.session.execute(select(Event).where(Event.id == event_model.id)).scalar_one()
        attendee_model1 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee_model2 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee_model3 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee_model4 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event.id))
        attendee1 = db.session.execute(select(Attendee).where(Attendee.id == attendee_model1.id)).scalar_one()

        self.shopify_service.customers[ShopifyService.customer_gid(user_model.shopify_id)] = ShopifyCustomer(
            gid=ShopifyService.customer_gid(user_model.shopify_id),
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            email=user_model.email,
            tags=tags,
        )

        self.attendee_service.send_invites(
            attendee_ids=[
                attendee_model1.id,
                attendee_model2.id,
                attendee_model3.id,
                attendee_model4.id,
            ]
        )

        for attendee in self.attendee_service.get_invited_attendees_for_the_event(event_id=event.id):
            attendee_user = self.user_service.get_user_by_id(attendee.user_id)

            self.shopify_service.customers[ShopifyService.customer_gid(attendee_user.shopify_id)] = ShopifyCustomer(
                gid=ShopifyService.customer_gid(attendee_user.shopify_id),
                first_name=attendee_user.first_name,
                last_name=attendee_user.last_name,
                email=attendee_user.email,
                tags=["test3"],
            )

        # when
        lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("EVENT_UPDATED", event)},
                ]
            },
            FakeLambdaContext(),
        )

        users = db.session.execute(select(User)).scalars().all()

        for user in users:
            if user.email == user_model.email:  # event owner
                self.assertTrue(TAG_EVENT_OWNER_4_PLUS in user.meta.get("tags", []))
            else:
                self.assertTrue(TAG_MEMBER_OF_4_PLUS_EVENT in user.meta.get("tags", []))

        # when
        self.attendee_service.deactivate_attendee(attendee_id=attendee_model1.id)

        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("ATTENDEE_UPDATED", attendee1)},
                ]
            },
            FakeLambdaContext(),
        )

        users = db.session.execute(select(User)).scalars().all()

        for user in users:
            self.assertFalse(TAG_MEMBER_OF_4_PLUS_EVENT in user.meta.get("tags", []))
            self.assertFalse(TAG_EVENT_OWNER_4_PLUS in user.meta.get("tags", []))

        self.assertEqual(response["statusCode"], 200)

    def test_one_attendee_belongs_to_2_events(self):
        # given
        tags1 = ["test1"]
        tags2 = ["test2"]

        user_model1 = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags1}))
        user_model2 = self.user_service.create_user(fixtures.create_user_request(meta={"tags": tags2}))

        event_model1 = self.event_service.create_event(fixtures.create_event_request(user_id=user_model1.id))
        event_model2 = self.event_service.create_event(fixtures.create_event_request(user_id=user_model2.id))

        event1 = db.session.execute(select(Event).where(Event.id == event_model1.id)).scalar_one()
        event2 = db.session.execute(select(Event).where(Event.id == event_model2.id)).scalar_one()

        attendee_email = utils.generate_email()

        attendee_model1 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event1.id, email=attendee_email)
        )
        attendee_model2 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event1.id))
        attendee_model3 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event1.id))
        attendee_model4 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event1.id))
        attendee_model5 = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event2.id, email=attendee_email)
        )
        attendee_model6 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event2.id))
        attendee_model7 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event2.id))
        attendee_model8 = self.attendee_service.create_attendee(fixtures.create_attendee_request(event_id=event2.id))
        attendee_1 = db.session.execute(select(Attendee).where(Attendee.id == attendee_model1.id)).scalar_one()

        self.shopify_service.customers[ShopifyService.customer_gid(user_model1.shopify_id)] = ShopifyCustomer(
            gid=ShopifyService.customer_gid(user_model1.shopify_id),
            first_name=user_model1.first_name,
            last_name=user_model1.last_name,
            email=user_model1.email,
            tags=tags1,
        )
        self.shopify_service.customers[ShopifyService.customer_gid(user_model2.shopify_id)] = ShopifyCustomer(
            gid=ShopifyService.customer_gid(user_model2.shopify_id),
            first_name=user_model2.first_name,
            last_name=user_model2.last_name,
            email=user_model2.email,
            tags=tags2,
        )

        self.attendee_service.send_invites(
            attendee_ids=[
                attendee_model1.id,
                attendee_model2.id,
                attendee_model3.id,
                attendee_model4.id,
                attendee_model5.id,
                attendee_model6.id,
                attendee_model7.id,
                attendee_model8.id,
            ]
        )

        for attendee in self.attendee_service.get_invited_attendees_for_the_event(event_id=event1.id):
            attendee_user = self.user_service.get_user_by_id(attendee.user_id)
            self.shopify_service.customers[ShopifyService.customer_gid(attendee_user.shopify_id)] = ShopifyCustomer(
                gid=ShopifyService.customer_gid(attendee_user.shopify_id),
                first_name=attendee_user.first_name,
                last_name=attendee_user.last_name,
                email=attendee_user.email,
                tags=["test3"],
            )

        for attendee in self.attendee_service.get_invited_attendees_for_the_event(event_id=event2.id):
            attendee_user = self.user_service.get_user_by_id(attendee.user_id)
            self.shopify_service.customers[ShopifyService.customer_gid(attendee_user.shopify_id)] = ShopifyCustomer(
                gid=ShopifyService.customer_gid(attendee_user.shopify_id),
                first_name=attendee_user.first_name,
                last_name=attendee_user.last_name,
                email=attendee_user.email,
                tags=["test4"],
            )

        # when
        lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("EVENT_UPDATED", event1)},
                ]
            },
            FakeLambdaContext(),
        )

        users = db.session.execute(select(User)).scalars().all()

        for user in users:
            if user.email in [
                attendee_model1.email,
                attendee_model2.email,
                attendee_model3.email,
                attendee_model4.email,
            ]:
                self.assertTrue(TAG_MEMBER_OF_4_PLUS_EVENT in user.meta.get("tags", []))
            else:
                self.assertFalse(TAG_MEMBER_OF_4_PLUS_EVENT in user.meta.get("tags", []))

            if user.email == user_model1.email:
                self.assertTrue(TAG_EVENT_OWNER_4_PLUS in user.meta.get("tags", []))
            else:
                self.assertFalse(TAG_EVENT_OWNER_4_PLUS in user.meta.get("tags", []))

        # when
        self.attendee_service.deactivate_attendee(attendee_id=attendee_model1.id)

        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("ATTENDEE_UPDATED", attendee_1)},
                ]
            },
            FakeLambdaContext(),
        )

        users = db.session.execute(select(User)).scalars().all()

        for user in users:
            if user.email == attendee_email:
                self.assertTrue(TAG_MEMBER_OF_4_PLUS_EVENT in user.meta.get("tags", []))
                self.assertFalse(TAG_EVENT_OWNER_4_PLUS in user.meta.get("tags", []))
            else:
                self.assertFalse(TAG_MEMBER_OF_4_PLUS_EVENT in user.meta.get("tags", []))
                self.assertFalse(TAG_EVENT_OWNER_4_PLUS in user.meta.get("tags", []))

        self.assertEqual(response["statusCode"], 200)

    def test_attendee_updated_but_no_look_associated(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, user_id=attendee_user.id)
        )

        # when
        self.attendee_service.update_attendee(
            attendee.id, UpdateAttendeeModel(first_name=str(utils.generate_unique_name()))
        )
        db_attendee = db.session.execute(select(Attendee).where(Attendee.id == attendee.id)).scalar_one()
        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("ATTENDEE_UPDATED", db_attendee)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]
        self.assertEqual(audit_log_event.type, "ATTENDEE_UPDATED")
        self.assertEqual(response["statusCode"], 200)

    def test_attendee_removed_but_no_look_associated(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(event_id=event.id, user_id=attendee_user.id)
        )

        # when
        self.attendee_service.deactivate_attendee(attendee_id=attendee.id)
        db_attendee = db.session.execute(select(Attendee).where(Attendee.id == attendee.id)).scalar_one()
        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("ATTENDEE_UPDATED", db_attendee)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]
        self.assertEqual(audit_log_event.type, "ATTENDEE_UPDATED")
        self.assertEqual(response["statusCode"], 200)

    def test_attendee_with_look_updated(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        look = self.look_service.create_look(
            fixtures.create_look_request(
                user_id=user.id,
                product_specs=self.create_look_test_product_specs_of_type_sku(),
            )
        )

        bundle_variant_id = look.product_specs["bundle"]["variant_id"]
        bundle_product = self.shopify_service.shopify_variants[bundle_variant_id]
        bundle_product.tags.remove(TAG_PRODUCT_NOT_LINKED_TO_EVENT)
        bundle_product.tags.append(TAG_PRODUCT_LINKED_TO_EVENT)

        self.assertTrue(TAG_PRODUCT_LINKED_TO_EVENT in bundle_product.tags)
        self.assertFalse(TAG_PRODUCT_NOT_LINKED_TO_EVENT in bundle_product.tags)

        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id,
                user_id=attendee_user.id,
                look_id=look.id,
            )
        )

        # when
        self.attendee_service.update_attendee(
            attendee.id, UpdateAttendeeModel(first_name=str(utils.generate_unique_name()))
        )
        attendee = db.session.execute(select(Attendee).where(Attendee.id == attendee.id)).scalar_one()
        response = lambda_handler(
            {
                "Records": [
                    {"body": fixtures.audit_log_queue_message("ATTENDEE_UPDATED", attendee)},
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]
        self.assertEqual(audit_log_event.type, "ATTENDEE_UPDATED")
        self.assertEqual(response["statusCode"], 200)

        bundle_variant_id = look.product_specs["bundle"]["variant_id"]
        bundle_product = self.shopify_service.shopify_variants[bundle_variant_id]

        self.assertTrue(TAG_PRODUCT_LINKED_TO_EVENT in bundle_product.tags)
        self.assertFalse(TAG_PRODUCT_NOT_LINKED_TO_EVENT in bundle_product.tags)

    def test_attendee_without_look_got_look_associated(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())
        look = self.look_service.create_look(
            fixtures.create_look_request(
                user_id=user.id,
                product_specs=self.create_look_test_product_specs_of_type_sku(),
            )
        )

        bundle_variant_id = look.product_specs["bundle"]["variant_id"]
        bundle_product = self.shopify_service.shopify_variants[bundle_variant_id]
        bundle_product.tags.remove(TAG_PRODUCT_NOT_LINKED_TO_EVENT)
        bundle_product.tags.append(TAG_PRODUCT_LINKED_TO_EVENT)

        self.assertTrue(TAG_PRODUCT_LINKED_TO_EVENT in bundle_product.tags)
        self.assertFalse(TAG_PRODUCT_NOT_LINKED_TO_EVENT in bundle_product.tags)

        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id,
                user_id=attendee_user.id,
            )
        )

        # when
        self.attendee_service.update_attendee(attendee.id, UpdateAttendeeModel(look_id=look.id))
        attendee = db.session.execute(select(Attendee).where(Attendee.id == attendee.id)).scalar_one()
        response = lambda_handler(
            {
                "Records": [
                    {
                        "body": fixtures.audit_log_queue_message(
                            "ATTENDEE_UPDATED", attendee, {}, {"look_id": {"before": None, "after": str(look.id)}}
                        )
                    },
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]
        self.assertEqual(audit_log_event.type, "ATTENDEE_UPDATED")
        self.assertEqual(response["statusCode"], 200)

        bundle_variant_id = look.product_specs["bundle"]["variant_id"]
        bundle_product = self.shopify_service.shopify_variants[bundle_variant_id]

        self.assertTrue(TAG_PRODUCT_LINKED_TO_EVENT in bundle_product.tags)
        self.assertFalse(TAG_PRODUCT_NOT_LINKED_TO_EVENT in bundle_product.tags)

    def test_attendee_with_look_got_look_changed(self):
        # given
        user = self.user_service.create_user(fixtures.create_user_request())
        event = self.event_service.create_event(fixtures.create_event_request(user_id=user.id))
        attendee_user = self.user_service.create_user(fixtures.create_user_request())

        look1 = self.look_service.create_look(
            fixtures.create_look_request(
                user_id=user.id,
                product_specs=self.create_look_test_product_specs_of_type_sku(),
            )
        )
        look2 = self.look_service.create_look(
            fixtures.create_look_request(
                user_id=user.id,
                product_specs=self.create_look_test_product_specs_of_type_sku(),
            )
        )

        bundle_product1 = self.shopify_service.shopify_variants[look1.product_specs["bundle"]["variant_id"]]
        bundle_product1.tags.remove(TAG_PRODUCT_NOT_LINKED_TO_EVENT)
        bundle_product1.tags.append(TAG_PRODUCT_LINKED_TO_EVENT)
        bundle_product2 = self.shopify_service.shopify_variants[look2.product_specs["bundle"]["variant_id"]]

        self.assertTrue(TAG_PRODUCT_LINKED_TO_EVENT in bundle_product1.tags)
        self.assertFalse(TAG_PRODUCT_NOT_LINKED_TO_EVENT in bundle_product1.tags)
        self.assertTrue(TAG_PRODUCT_NOT_LINKED_TO_EVENT in bundle_product2.tags)
        self.assertFalse(TAG_PRODUCT_LINKED_TO_EVENT in bundle_product2.tags)

        attendee = self.attendee_service.create_attendee(
            fixtures.create_attendee_request(
                event_id=event.id,
                user_id=attendee_user.id,
                look_id=look1.id,
            )
        )

        # when
        self.attendee_service.update_attendee(attendee.id, UpdateAttendeeModel(look_id=look2.id))
        attendee = db.session.execute(select(Attendee).where(Attendee.id == attendee.id)).scalar_one()
        response = lambda_handler(
            {
                "Records": [
                    {
                        "body": fixtures.audit_log_queue_message(
                            "ATTENDEE_UPDATED",
                            attendee,
                            {},
                            {"look_id": {"before": str(look1.id), "after": str(look2.id)}},
                        )
                    },
                ]
            },
            FakeLambdaContext(),
        )

        # then
        audit_logs = db.session.execute(select(AuditLog)).scalars().all()
        audit_log_event = audit_logs[0]
        self.assertEqual(audit_log_event.type, "ATTENDEE_UPDATED")
        self.assertEqual(response["statusCode"], 200)

        bundle_product1 = self.shopify_service.shopify_variants[look1.product_specs["bundle"]["variant_id"]]
        bundle_product2 = self.shopify_service.shopify_variants[look2.product_specs["bundle"]["variant_id"]]

        self.assertTrue(TAG_PRODUCT_NOT_LINKED_TO_EVENT in bundle_product1.tags)
        self.assertFalse(TAG_PRODUCT_LINKED_TO_EVENT in bundle_product1.tags)
        self.assertTrue(TAG_PRODUCT_LINKED_TO_EVENT in bundle_product2.tags)
        self.assertFalse(TAG_PRODUCT_NOT_LINKED_TO_EVENT in bundle_product2.tags)
