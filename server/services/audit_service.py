import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Set

from server.database.database_manager import db
from server.database.models import (
    AuditLog,
)
from server.models.audit_model import AuditLogMessage
from server.services.attendee_service import AttendeeService
from server.services.event_service import EventService
from server.services.integrations.shopify_service import ShopifyService, AbstractShopifyService
from server.services.user_activity_log_service import UserActivityLogService
from server.services.user_service import UserService

logger = logging.getLogger(__name__)

TAG_EVENT_OWNER_4_PLUS = "event_owner_4_plus"
TAG_MEMBER_OF_4_PLUS_EVENT = "member_of_4_plus_event"


class AuditLogService:
    def __init__(
        self,
        shopify_service: AbstractShopifyService,
        user_service: UserService,
        attendee_service: AttendeeService,
        event_service: EventService,
        user_activity_log_service: UserActivityLogService,
    ):
        self.shopify_service = shopify_service
        self.user_service = user_service
        self.attendee_service = attendee_service
        self.event_service = event_service
        self.user_activity_log_service = user_activity_log_service

    @staticmethod
    def persist(audit_log_message: AuditLogMessage) -> None:
        try:
            db.session.add(
                AuditLog(
                    id=uuid.UUID(audit_log_message.id),
                    request=audit_log_message.request,
                    type=audit_log_message.type,
                    payload=audit_log_message.payload,
                    diff=audit_log_message.diff,
                    created_at=datetime.now(timezone.utc),
                )
            )
            db.session.commit()
        except Exception as e:
            logger.exception(f"Error persisting audit log message: {audit_log_message}")
            db.session.rollback()

    def process(self, audit_log_message: AuditLogMessage) -> None:
        self.persist(audit_log_message)

        if audit_log_message.type == "USER_CREATED":
            self.user_activity_log_service.user_created(audit_log_message)
        elif audit_log_message.type == "USER_UPDATED":
            self.user_activity_log_service.user_updated(audit_log_message)
        elif audit_log_message.type == "EVENT_UPDATED":
            self.__tag_customers_on_event_updated(audit_log_message)
        elif audit_log_message.type == "ATTENDEE_UPDATED":
            self.__tag_customers_on_attendee_updated(audit_log_message)

    def __tag_customers_on_event_updated(self, audit_log_message: AuditLogMessage):
        user_id = audit_log_message.payload.get("user_id")
        event_id = audit_log_message.payload.get("id")

        user_tags_that_should_be_present = {}
        user_tags_that_should_not_be_present = {}

        logger.info(f"Processing 'EVENT_UPDATED' message for user {user_id} and event {event_id}")

        events = self.event_service.get_user_owned_events_with_n_attendees(user_id, 4)

        if events:
            user_tags_that_should_be_present[user_id] = {TAG_EVENT_OWNER_4_PLUS}
        else:
            user_tags_that_should_not_be_present[user_id] = {TAG_EVENT_OWNER_4_PLUS}

        attendees = self.attendee_service.get_invited_attendees_for_the_event(uuid.UUID(event_id))

        for attendee in attendees:
            events = self.event_service.get_user_member_events_with_n_attendees(attendee.user_id, 4)

            user_tags_that_should_be_present.setdefault(attendee.user_id, set())
            user_tags_that_should_not_be_present.setdefault(attendee.user_id, set())

            if events:
                if not user_tags_that_should_be_present.get(attendee.user_id):
                    user_tags_that_should_be_present[attendee.user_id] = set()

                user_tags_that_should_be_present[attendee.user_id].add(TAG_MEMBER_OF_4_PLUS_EVENT)
            else:
                if not user_tags_that_should_not_be_present.get(attendee.user_id):
                    user_tags_that_should_not_be_present[attendee.user_id] = set()

                user_tags_that_should_not_be_present[attendee.user_id].add(TAG_MEMBER_OF_4_PLUS_EVENT)

        if user_tags_that_should_be_present:
            self.__add_tags(user_tags_that_should_be_present)

        if user_tags_that_should_not_be_present:
            self.__remove_tags(user_tags_that_should_not_be_present)

    def __tag_customers_on_attendee_updated(self, audit_log_message: AuditLogMessage):
        event_id = audit_log_message.payload.get("event_id")
        user_id = audit_log_message.payload.get("user_id")
        attendee_id = audit_log_message.payload.get("id")
        attendee_is_active = audit_log_message.payload.get("is_active")

        if not user_id:
            # nothing to do, we don't care about attendees without user_id (not invited)
            return

        event = self.event_service.get_event_by_id(uuid.UUID(event_id))
        event_owner_user_id = event.user_id

        logger.info(f"Processing 'ATTENDEE_UPDATED' message for user {user_id}")

        user_tags_that_should_be_present: Dict[uuid.UUID, Set[str]] = {}
        user_tags_that_should_not_be_present: Dict[uuid.UUID, Set[str]] = {}

        events = self.event_service.get_user_owned_events_with_n_attendees(event_owner_user_id, 4)

        if events:
            user_tags_that_should_be_present[event_owner_user_id] = {TAG_EVENT_OWNER_4_PLUS}
        else:
            user_tags_that_should_not_be_present[event_owner_user_id] = {TAG_EVENT_OWNER_4_PLUS}

        attendees = self.attendee_service.get_invited_attendees_for_the_event(uuid.UUID(event_id))

        if not attendee_is_active:
            attendees.append(self.attendee_service.get_attendee_by_id(uuid.UUID(attendee_id), False))

        for attendee in attendees:
            events = self.event_service.get_user_member_events_with_n_attendees(attendee.user_id, 4)

            if events:
                if not user_tags_that_should_be_present.get(attendee.user_id):
                    user_tags_that_should_be_present[attendee.user_id] = set()

                user_tags_that_should_be_present[attendee.user_id].add(TAG_MEMBER_OF_4_PLUS_EVENT)
            else:
                if not user_tags_that_should_not_be_present.get(attendee.user_id):
                    user_tags_that_should_not_be_present[attendee.user_id] = set()

                user_tags_that_should_not_be_present[attendee.user_id].add(TAG_MEMBER_OF_4_PLUS_EVENT)

        if user_tags_that_should_be_present:
            self.__add_tags(user_tags_that_should_be_present)

        if user_tags_that_should_not_be_present:
            self.__remove_tags(user_tags_that_should_not_be_present)

    def __add_tags(self, user_tags_that_should_be_present: Dict[uuid.UUID, Set[str]]):
        for user_id, tags in user_tags_that_should_be_present.items():
            user = self.user_service.get_user_by_id(user_id)

            current_user_tags = set(user.meta.get("tags", []))

            if tags.issubset(current_user_tags):
                logger.info(f"User {user.id}/{user.shopify_id} already has tags {tags}. Skipping ...")
            else:
                logger.info(f"User {user.id}/{user.shopify_id} does not have tags {tags}. Adding ...")
                current_user_tags.update(tags)

                self.shopify_service.add_tags(ShopifyService.customer_gid(int(user.shopify_id)), current_user_tags)
                self.user_service.add_meta_tag(user.id, current_user_tags)

    def __remove_tags(self, user_tags_that_should_not_be_present: Dict[uuid.UUID, Set[str]]):
        for user_id, tags in user_tags_that_should_not_be_present.items():
            user = self.user_service.get_user_by_id(user_id)

            current_user_tags = set(user.meta.get("tags", []))

            if not tags.intersection(current_user_tags):
                logger.info(f"User {user.id}/{user.shopify_id} does not have tags {tags}. Skipping ...")
            else:
                logger.info(f"User {user.id}/{user.shopify_id} has tags {tags}. Removing ...")
                current_user_tags.difference_update(tags)

                self.shopify_service.remove_tags(ShopifyService.customer_gid(int(user.shopify_id)), tags)
                self.user_service.remove_meta_tag(user.id, tags)
