import json
import uuid
from typing import Dict, Set

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from server.flask_app import FlaskApp
from server.handlers import init_sentry
from server.models.audit_model import AuditLogMessage
from server.services.attendee_service import AttendeeService
from server.services.audit_service import AuditLogService
from server.services.event_service import EventService
from server.services.integrations.shopify_service import ShopifyService, AbstractShopifyService
from server.services.user_service import UserService

TAG_EVENT_OWNER_4_PLUS = "event_owner_4_plus"
TAG_MEMBER_OF_4_PLUS_EVENT = "member_of_4_plus_event"

init_sentry()

logger = Logger(service="audit-log-processor")


class FakeLambdaContext(LambdaContext):
    def __init__(self):
        self._function_name = "test_function"
        self._memory_limit_in_mb = 128
        self._invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test_function"
        self._aws_request_id = "test-request-id"


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext):
    shopify_service = FlaskApp().current().shopify_service if __in_test_context(context) else ShopifyService()
    audit_log_service = AuditLogService()
    user_service = UserService(shopify_service)
    attendee_service = AttendeeService(shopify_service, user_service, None, None, None)
    event_service = EventService()

    for record in event.get("Records", []):
        message = record.get("body", "{}")

        try:
            audit_log_message = AuditLogMessage.from_string(message)

            __persist_audit_log(audit_log_service, message)

            if audit_log_message.type == "EVENT_UPDATED":
                __handle_event_updated(
                    shopify_service, user_service, event_service, attendee_service, audit_log_message
                )
            elif audit_log_message.type == "ATTENDEE_UPDATED":
                __handle_attendee_updated(
                    shopify_service, user_service, event_service, attendee_service, audit_log_message
                )
        except Exception as e:
            logger.exception(f"Error processing audit message: {message}")

    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}


def __in_test_context(context) -> bool:
    return isinstance(context, FakeLambdaContext)


def __persist_audit_log(audit_log_service: AuditLogService, message: str) -> None:
    audit_log_message = AuditLogMessage.from_string(message)
    audit_log_service.save_audit_log(audit_log_message)


def __handle_event_updated(
    shopify_service: AbstractShopifyService,
    user_service: UserService,
    event_service: EventService,
    attendee_service: AttendeeService,
    audit_log_message: AuditLogMessage,
):
    user_id = audit_log_message.payload.get("user_id")
    event_id = audit_log_message.payload.get("id")

    user_tags_that_should_be_present = {}
    user_tags_that_should_not_be_present = {}

    logger.info(f"Processing 'EVENT_UPDATED' message for user {user_id} and event {event_id}")

    events = event_service.get_user_owned_events_with_n_attendees(user_id, 4)

    if events:
        user_tags_that_should_be_present[user_id] = {TAG_EVENT_OWNER_4_PLUS}
    else:
        user_tags_that_should_not_be_present[user_id] = {TAG_EVENT_OWNER_4_PLUS}

    attendees = attendee_service.get_invited_attendees_for_the_event(uuid.UUID(event_id))

    for attendee in attendees:
        events = event_service.get_user_member_events_with_n_attendees(attendee.user_id, 4)

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
        __add_tags(user_tags_that_should_be_present, user_service, shopify_service)

    if user_tags_that_should_not_be_present:
        __remove_tags(user_tags_that_should_not_be_present, user_service, shopify_service)


def __handle_attendee_updated(
    shopify_service: AbstractShopifyService,
    user_service: UserService,
    event_service: EventService,
    attendee_service: AttendeeService,
    audit_log_message: AuditLogMessage,
):
    event_id = audit_log_message.payload.get("event_id")
    user_id = audit_log_message.payload.get("user_id")
    attendee_id = audit_log_message.payload.get("id")
    attendee_is_active = audit_log_message.payload.get("is_active")

    if not user_id:
        # nothing to do, we don't care about attendees without user_id (not invited)
        return

    event = event_service.get_event_by_id(uuid.UUID(event_id))
    event_owner_user_id = event.user_id

    logger.info(f"Processing 'ATTENDEE_UPDATED' message for user {user_id}")

    user_tags_that_should_be_present: Dict[uuid.UUID, Set[str]] = {}
    user_tags_that_should_not_be_present: Dict[uuid.UUID, Set[str]] = {}

    events = event_service.get_user_owned_events_with_n_attendees(event_owner_user_id, 4)

    if events:
        user_tags_that_should_be_present[event_owner_user_id] = {TAG_EVENT_OWNER_4_PLUS}
    else:
        user_tags_that_should_not_be_present[event_owner_user_id] = {TAG_EVENT_OWNER_4_PLUS}

    attendees = attendee_service.get_invited_attendees_for_the_event(uuid.UUID(event_id))

    if not attendee_is_active:
        attendees.append(attendee_service.get_attendee_by_id(uuid.UUID(attendee_id), False))

    for attendee in attendees:
        events = event_service.get_user_member_events_with_n_attendees(attendee.user_id, 4)

        if events:
            if not user_tags_that_should_be_present.get(attendee.user_id):
                user_tags_that_should_be_present[attendee.user_id] = set()

            user_tags_that_should_be_present[attendee.user_id].add(TAG_MEMBER_OF_4_PLUS_EVENT)
        else:
            if not user_tags_that_should_not_be_present.get(attendee.user_id):
                user_tags_that_should_not_be_present[attendee.user_id] = set()

            user_tags_that_should_not_be_present[attendee.user_id].add(TAG_MEMBER_OF_4_PLUS_EVENT)

    if user_tags_that_should_be_present:
        __add_tags(user_tags_that_should_be_present, user_service, shopify_service)

    if user_tags_that_should_not_be_present:
        __remove_tags(user_tags_that_should_not_be_present, user_service, shopify_service)


def __add_tags(
    user_tags_that_should_be_present: Dict[uuid.UUID, Set[str]],
    user_service: UserService,
    shopify_service: AbstractShopifyService,
):
    for user_id, tags in user_tags_that_should_be_present.items():
        user = user_service.get_user_by_id(user_id)

        current_user_tags = set(user.meta.get("tags", []))

        if tags.issubset(current_user_tags):
            logger.info(f"User {user.id}/{user.shopify_id} already has tags {tags}. Skipping ...")
        else:
            logger.info(f"User {user.id}/{user.shopify_id} does not have tags {tags}. Adding ...")
            current_user_tags.update(tags)

            shopify_service.add_tags(ShopifyService.customer_gid(user.shopify_id), current_user_tags)
            user_service.add_meta_tag(user.id, current_user_tags)


def __remove_tags(
    user_tags_that_should_not_be_present: Dict[uuid.UUID, Set[str]],
    user_service: UserService,
    shopify_service: AbstractShopifyService,
):
    for user_id, tags in user_tags_that_should_not_be_present.items():
        user = user_service.get_user_by_id(user_id)

        current_user_tags = set(user.meta.get("tags", []))

        if not tags.intersection(current_user_tags):
            logger.info(f"User {user.id}/{user.shopify_id} does not have tags {tags}. Skipping ...")
        else:
            logger.info(f"User {user.id}/{user.shopify_id} has tags {tags}. Removing ...")
            current_user_tags.difference_update(tags)

            shopify_service.remove_tags(ShopifyService.customer_gid(user.shopify_id), tags)
            user_service.remove_meta_tag(user.id, tags)
