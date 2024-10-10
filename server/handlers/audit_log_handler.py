import json

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from server.flask_app import FlaskApp
from server.handlers import init_sentry
from server.models.audit_model import AuditLogMessage
from server.models.user_model import UserModel
from server.services.audit_service import AuditLogService
from server.services.event_service import EventService
from server.services.integrations.shopify_service import ShopifyService, AbstractShopifyService
from server.services.user_service import UserService

TAG_EVENT_OWNER_4_PLUS = "event_owner_4_plus"

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
    event_service = EventService()

    for record in event.get("Records", []):
        message = record.get("body", "{}")

        try:
            audit_log_message = AuditLogMessage.from_string(message)

            __persist_audit_log(audit_log_service, message)

            __tag_customers(shopify_service, user_service, event_service, audit_log_message)
        except Exception as e:
            logger.exception(f"Error processing audit message: {message}")

    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}


def __in_test_context(context) -> bool:
    return isinstance(context, FakeLambdaContext)


def __persist_audit_log(audit_log_service: AuditLogService, message: str) -> None:
    audit_log_message = AuditLogMessage.from_string(message)
    audit_log_service.save_audit_log(audit_log_message)


def __tag_customers(
    shopify_service: AbstractShopifyService,
    user_service: UserService,
    event_service: EventService,
    audit_log_message: AuditLogMessage,
) -> None:
    if audit_log_message.type == "EVENT_UPDATED":
        user_id = audit_log_message.payload.get("user_id")
        user = user_service.get_user_by_id(user_id)

        if not user.shopify_id:
            return

        events = event_service.get_user_owned_events_with_n_attendees(user_id, 4)

        logger.info(f"Processing 'EVENT_UPDATED' message for user {user_id}/{user.shopify_id}")

        if events:
            __add_4_plus_attendee_tags(shopify_service, user_service, user)
        else:
            __remove_4_plus_attendee_tags(shopify_service, user_service, user)
    elif audit_log_message.type == "ATTENDEE_UPDATED":
        event_id = audit_log_message.payload.get("event_id")
        user_id = event_service.get_event_by_id(event_id).user_id

        if not user_id:
            return

        user = user_service.get_user_by_id(user_id)

        if not user.shopify_id:
            return

        events = event_service.get_user_owned_events_with_n_attendees(user_id, 4)

        logger.info(f"Processing 'ATTENDEE_CREATED/ATTENDEE_UPDATED' message for user {user_id}/{user.shopify_id}")

        if events:
            __add_4_plus_attendee_tags(shopify_service, user_service, user)
        else:
            __remove_4_plus_attendee_tags(shopify_service, user_service, user)


def __add_4_plus_attendee_tags(shopify_service: AbstractShopifyService, user_service: UserService, user: UserModel):
    user_tags = set(user.meta.get("tags", []))

    if TAG_EVENT_OWNER_4_PLUS in user_tags:
        logger.info(f"User {user.id}/{user.shopify_id} already has tag {TAG_EVENT_OWNER_4_PLUS}. Skipping ...")
    else:
        logger.info(
            f"User {user.id}/{user.shopify_id} has events with 4+ attendees. Adding tag {TAG_EVENT_OWNER_4_PLUS}"
        )
        shopify_service.add_tags(ShopifyService.customer_gid(user.shopify_id), [TAG_EVENT_OWNER_4_PLUS])
        user_service.add_meta_tag(user.id, TAG_EVENT_OWNER_4_PLUS)


def __remove_4_plus_attendee_tags(shopify_service: AbstractShopifyService, user_service: UserService, user: UserModel):
    user_tags = set(user.meta.get("tags", []))

    if TAG_EVENT_OWNER_4_PLUS in user_tags:
        logger.info(f"User {user.id}/{user.shopify_id} has tag {TAG_EVENT_OWNER_4_PLUS}. Removing ...")
        shopify_service.remove_tags(ShopifyService.customer_gid(user.shopify_id), [TAG_EVENT_OWNER_4_PLUS])
        user_service.remove_meta_tag(user.id, TAG_EVENT_OWNER_4_PLUS)
    else:
        logger.info(f"User {user.id}/{user.shopify_id} does not have tag {TAG_EVENT_OWNER_4_PLUS}. Skipping ...")
