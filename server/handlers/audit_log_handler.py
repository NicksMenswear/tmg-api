import json
import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from server.flask_app import FlaskApp
from server.handlers import init_sentry
from server.models.audit_log_model import AuditLogMessage
from server.services.attendee_service import AttendeeService
from server.services.audit_service import AuditLogService
from server.services.event_service import EventService
from server.services.integrations.shopify_service import ShopifyService
from server.services.look_service import LookService
from server.services.order_service import OrderService
from server.services.role_service import RoleService
from server.services.tagging_service import TaggingService
from server.services.user_activity_log_service import UserActivityLogService
from server.services.user_service import UserService

init_sentry()

logger = Logger(service="audit-log-processor")

ONLINE_STORE_SALES_CHANNEL_ID = os.getenv("online_store_sales_channel_id", "gid://shopify/Publication/94480072835")


class FakeLambdaContext(LambdaContext):
    def __init__(self):
        self._function_name = "test_function"
        self._memory_limit_in_mb = 128
        self._invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test_function"
        self._aws_request_id = "test-request-id"


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext):
    shopify_service = (
        FlaskApp().current().shopify_service
        if __in_test_context(context)
        else ShopifyService(ONLINE_STORE_SALES_CHANNEL_ID)
    )
    user_service = UserService(shopify_service)
    attendee_service = AttendeeService(shopify_service, user_service, None, None, None)
    event_service = EventService()
    role_service = RoleService()
    order_service = OrderService(user_service)
    look_service = LookService(user_service, None, None)
    user_activity_log_service = UserActivityLogService(
        user_service, event_service, attendee_service, role_service, look_service, order_service
    )
    tagging_service = TaggingService(
        user_service,
        event_service,
        attendee_service,
        look_service,
        shopify_service,
    )
    audit_log_service = AuditLogService(tagging_service, user_activity_log_service)

    for record in event.get("Records", []):
        message = record.get("body", "{}")

        try:
            audit_log_service.process(AuditLogMessage.from_string(message))
        except Exception:
            logger.exception(f"Error processing audit message: {message}")

    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}


def __in_test_context(context) -> bool:
    return isinstance(context, FakeLambdaContext)
