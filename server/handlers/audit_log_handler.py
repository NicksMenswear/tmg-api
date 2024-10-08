import json
import logging

from server.flask_app import FlaskApp
from server.logs import init_logging
from server.models.audit_model import AuditLogMessage
from server.services.audit_service import AuditLogService
from server.services.event_service import EventService
from server.services.integrations.shopify_service import ShopifyService, AbstractShopifyService
from server.services.user_service import UserService

init_logging("tmg-audit-logs-processing", debug=True)

logger = logging.getLogger(__name__)

TAG_EVENT_OWNER_4_PLUS = "event_owner_4_plus"


def process_messages(event, context):
    if context.get("testing", False):
        shopify_service = FlaskApp().current().shopify_service
    else:
        shopify_service = ShopifyService()

    audit_log_service = AuditLogService()
    user_service = UserService(shopify_service)
    event_service = EventService()

    for record in event.get("Records", []):
        message = record.get("body", "{}")

        try:
            audit_log_message = AuditLogMessage.from_string(message)

            __persist_audit_log(audit_log_service, message)

            __tag_customers_event_owner_4_plus(shopify_service, user_service, event_service, audit_log_message)
        except Exception as e:
            print(f"Error processing message: {message}: {str(e)}")  # remove this print once logging will work
            logger.exception(f"Error processing message: {message}", e)

    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}


def __persist_audit_log(audit_log_service: AuditLogService, message: str) -> None:
    audit_log_message = AuditLogMessage.from_string(message)
    audit_log_service.save_audit_log(audit_log_message)


def __tag_customers_event_owner_4_plus(
    shopify_service: AbstractShopifyService,
    user_service: UserService,
    event_service: EventService,
    audit_log_message: AuditLogMessage,
) -> None:
    if audit_log_message.type == "EVENT_UPDATED":
        user_id = audit_log_message.payload.get("user_id")
        user = user_service.get_user_by_id(user_id)

        events = event_service.get_user_owned_events_with_n_attendees(user_id, 4)

        if not user.shopify_id:
            return

        if events:
            shopify_service.add_tags(ShopifyService.customer_gid(user.shopify_id), [TAG_EVENT_OWNER_4_PLUS])
        else:
            shopify_service.remove_tags(ShopifyService.customer_gid(user.shopify_id), [TAG_EVENT_OWNER_4_PLUS])
    elif audit_log_message.type == "ATTENDEE_CREATED" or audit_log_message.type == "ATTENDEE_UPDATED":
        event_id = audit_log_message.payload.get("event_id")
        user_id = event_service.get_event_by_id(event_id).user_id

        if not user_id:
            return

        user = user_service.get_user_by_id(user_id)

        if not user.shopify_id:
            return

        events = event_service.get_user_owned_events_with_n_attendees(user_id, 4)

        if events:
            shopify_service.add_tags(ShopifyService.customer_gid(user.shopify_id), [TAG_EVENT_OWNER_4_PLUS])
        else:
            shopify_service.remove_tags(ShopifyService.customer_gid(user.shopify_id), [TAG_EVENT_OWNER_4_PLUS])
