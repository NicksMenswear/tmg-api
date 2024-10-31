import logging
import uuid

from server.models.audit_log_model import AuditLogMessage
from server.models.event_model import EventModel
from server.services import NotFoundError
from server.services.attendee_service import AttendeeService
from server.services.event_service import EventService
from server.services.integrations.shopify_service import ShopifyService, AbstractShopifyService
from server.services.look_service import LookService
from server.services.user_service import UserService

logger = logging.getLogger(__name__)

TAG_EVENT_OWNER_4_PLUS = "event_owner_4_plus"
TAG_MEMBER_OF_4_PLUS_EVENT = "member_of_4_plus_event"
TAG_PRODUCT_LINKED_TO_EVENT = "linked_to_event"
TAG_PRODUCT_NOT_LINKED_TO_EVENT = "not_linked_to_event"


class ShopifyTaggingService:
    def __init__(
        self,
        user_service: UserService,
        event_service: EventService,
        attendee_service: AttendeeService,
        look_service: LookService,
        shopify_service: AbstractShopifyService,
    ):
        self.__user_service = user_service
        self.__event_service = event_service
        self.__attendee_service = attendee_service
        self.__look_service = look_service
        self.__shopify_service = shopify_service

    def tag_customers_on_event_updated(self, audit_log_message: AuditLogMessage):
        user_id = audit_log_message.payload.get("user_id")
        event_id = audit_log_message.payload.get("id")

        user_tags_that_should_be_present = {}
        user_tags_that_should_not_be_present = {}

        logger.info(f"Processing 'EVENT_UPDATED' message for user {user_id} and event {event_id}")

        events = self.__event_service.get_user_owned_events_with_n_attendees(user_id, 4)

        if events:
            user_tags_that_should_be_present[user_id] = {TAG_EVENT_OWNER_4_PLUS}
        else:
            user_tags_that_should_not_be_present[user_id] = {TAG_EVENT_OWNER_4_PLUS}

        attendees = self.__attendee_service.get_invited_attendees_for_the_event(uuid.UUID(event_id))

        for attendee in attendees:
            events = self.__event_service.get_user_member_events_with_n_attendees(attendee.user_id, 4)

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
            self.__add_tags_to_customers(user_tags_that_should_be_present)

        if user_tags_that_should_not_be_present:
            self.__remove_tags_from_customers(user_tags_that_should_not_be_present)

    def tag_customers_on_attendee_updated(self, audit_log_message: AuditLogMessage):
        event_id = audit_log_message.payload.get("event_id")
        user_id = audit_log_message.payload.get("user_id")
        attendee_id = audit_log_message.payload.get("id")
        attendee_is_active = audit_log_message.payload.get("is_active")

        if not user_id:
            # nothing to do, we don't care about attendees without user_id (not invited)
            return

        event = self.__event_service.get_event_by_id(uuid.UUID(event_id))
        event_owner_user_id = event.user_id

        logger.info(f"Processing 'ATTENDEE_UPDATED' message for user {user_id}")

        user_tags_that_should_be_present: dict[uuid.UUID, set[str]] = {}
        user_tags_that_should_not_be_present: dict[uuid.UUID, set[str]] = {}

        events = self.__event_service.get_user_owned_events_with_n_attendees(event_owner_user_id, 4)

        if events:
            user_tags_that_should_be_present[event_owner_user_id] = {TAG_EVENT_OWNER_4_PLUS}
        else:
            user_tags_that_should_not_be_present[event_owner_user_id] = {TAG_EVENT_OWNER_4_PLUS}

        attendees = self.__attendee_service.get_invited_attendees_for_the_event(uuid.UUID(event_id))

        if not attendee_is_active:
            attendees.append(self.__attendee_service.get_attendee_by_id(uuid.UUID(attendee_id), False))

        for attendee in attendees:
            events = self.__event_service.get_user_member_events_with_n_attendees(attendee.user_id, 4)

            if events:
                if not user_tags_that_should_be_present.get(attendee.user_id):
                    user_tags_that_should_be_present[attendee.user_id] = set()

                user_tags_that_should_be_present[attendee.user_id].add(TAG_MEMBER_OF_4_PLUS_EVENT)
            else:
                if not user_tags_that_should_not_be_present.get(attendee.user_id):
                    user_tags_that_should_not_be_present[attendee.user_id] = set()

                user_tags_that_should_not_be_present[attendee.user_id].add(TAG_MEMBER_OF_4_PLUS_EVENT)

        if user_tags_that_should_be_present:
            self.__add_tags_to_customers(user_tags_that_should_be_present)

        if user_tags_that_should_not_be_present:
            self.__remove_tags_from_customers(user_tags_that_should_not_be_present)

    def tag_products_on_event_updated(self, audit_log_message: AuditLogMessage):
        event_is_active = audit_log_message.payload.get("is_active")

        if event_is_active:  # event is still active so we don't need to do anything
            return

        event_id = audit_log_message.payload.get("id")
        event: EventModel = self.__event_service.get_event_by_id(uuid.UUID(event_id), True)

        if not event.looks:  # event has no looks
            return

        unique_looks = dict()

        for look in event.looks:
            unique_looks[look.id] = look

        for look_id, look in unique_looks.items():
            shopify_product_id = look.product_specs.get("bundle", {}).get("product_id")

            if not shopify_product_id:
                continue

            shopify_product_gid = ShopifyService.product_gid(int(shopify_product_id))

            attendees = self.__attendee_service.find_attendees_by_look_id(look.id)

            if attendees:
                self.__shopify_service.remove_tags(shopify_product_gid, {TAG_PRODUCT_LINKED_TO_EVENT})
            else:
                self.__shopify_service.add_tags(shopify_product_gid, {TAG_PRODUCT_NOT_LINKED_TO_EVENT})

    def tag_products_on_attendee_updated(self, audit_log_message: AuditLogMessage):
        attendee_is_active = audit_log_message.payload.get("is_active")
        look_id = audit_log_message.payload.get("look_id")
        diff = audit_log_message.diff

        look_ids_in_question = set()

        if not attendee_is_active:
            look_ids_in_question.add(look_id)

        if diff and diff.get("look_id"):
            look_id_before = diff.get("look_id", {}).get("before")

            if look_id_before:
                look_ids_in_question.add(look_id_before)

            look_id_after = diff.get("look_id", {}).get("after")

            if look_id_after:
                look_ids_in_question.add(look_id_after)

        if not look_ids_in_question:
            return

        for look_id in look_ids_in_question:
            try:
                look = self.__look_service.get_look_by_id(uuid.UUID(look_id))
            except NotFoundError:
                logger.error(f"Look {look_id} not found")
                continue

            shopify_product_id = look.product_specs.get("bundle", {}).get("product_id")

            if not shopify_product_id:
                continue

            shopify_product_gid = ShopifyService.product_gid(int(shopify_product_id))

            attendees = self.__attendee_service.find_attendees_by_look_id(uuid.UUID(look_id))

            if attendees:
                self.__shopify_service.add_tags(shopify_product_gid, {TAG_PRODUCT_LINKED_TO_EVENT})
            else:
                self.__shopify_service.add_tags(shopify_product_gid, {TAG_PRODUCT_NOT_LINKED_TO_EVENT})

    def __add_tags_to_customers(self, user_tags_that_should_be_present: dict[uuid.UUID, set[str]]):
        for user_id, tags in user_tags_that_should_be_present.items():
            user = self.__user_service.get_user_by_id(user_id)

            current_user_tags = set(user.meta.get("tags", []))

            if tags.issubset(current_user_tags):
                logger.info(f"User {user.id}/{user.shopify_id} already has tags {tags}. Skipping ...")
            else:
                logger.info(f"User {user.id}/{user.shopify_id} does not have tags {tags}. Adding ...")
                current_user_tags.update(tags)

                self.__shopify_service.add_tags(ShopifyService.customer_gid(int(user.shopify_id)), current_user_tags)
                self.__user_service.add_meta_tag(user.id, current_user_tags)

    def __remove_tags_from_customers(self, user_tags_that_should_not_be_present: dict[uuid.UUID, set[str]]):
        for user_id, tags in user_tags_that_should_not_be_present.items():
            user = self.__user_service.get_user_by_id(user_id)

            current_user_tags = set(user.meta.get("tags", []))

            if not tags.intersection(current_user_tags):
                logger.info(f"User {user.id}/{user.shopify_id} does not have tags {tags}. Skipping ...")
            else:
                logger.info(f"User {user.id}/{user.shopify_id} has tags {tags}. Removing ...")
                current_user_tags.difference_update(tags)

                self.__shopify_service.remove_tags(ShopifyService.customer_gid(int(user.shopify_id)), tags)
                self.__user_service.remove_meta_tag(user.id, tags)
