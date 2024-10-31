import logging
from datetime import datetime, timezone

from server.database.database_manager import db
from server.database.models import AuditLog
from server.models.audit_log_model import AuditLogMessage
from server.services.shoppify_tagging_service import ShopifyTaggingService
from server.services.user_activity_log_service import UserActivityLogService

logger = logging.getLogger(__name__)


class AuditLogService:
    def __init__(
        self,
        shopify_tagging_service: ShopifyTaggingService,
        user_activity_log_service: UserActivityLogService,
    ):
        self.shopify_tagging_service = shopify_tagging_service
        self.user_activity_log_service = user_activity_log_service

    def process(self, audit_log_message: AuditLogMessage) -> None:
        self.__persist(audit_log_message)

        if audit_log_message.type == "USER_CREATED":
            self.user_activity_log_service.user_created(audit_log_message)
        elif audit_log_message.type == "USER_UPDATED":
            self.user_activity_log_service.user_updated(audit_log_message)
        elif audit_log_message.type == "EVENT_CREATED":
            self.user_activity_log_service.event_created(audit_log_message)
        elif audit_log_message.type == "EVENT_UPDATED":
            self.user_activity_log_service.event_updated(audit_log_message)
            self.shopify_tagging_service.tag_customers_on_event_updated(audit_log_message)
            self.shopify_tagging_service.tag_products_on_event_updated(audit_log_message)
        elif audit_log_message.type == "ATTENDEE_CREATED":
            self.user_activity_log_service.attendee_created(audit_log_message)
        elif audit_log_message.type == "ATTENDEE_UPDATED":
            self.user_activity_log_service.attendee_updated(audit_log_message)
            self.shopify_tagging_service.tag_customers_on_attendee_updated(audit_log_message)
            self.shopify_tagging_service.tag_products_on_attendee_updated(audit_log_message)
        elif audit_log_message.type == "LOOK_CREATED":
            self.user_activity_log_service.look_created(audit_log_message)
        elif audit_log_message.type == "LOOK_UPDATED":
            self.user_activity_log_service.look_updated(audit_log_message)
        elif audit_log_message.type == "MEASUREMENT_CREATED":
            self.user_activity_log_service.measurements_created(audit_log_message)
        elif audit_log_message.type == "SIZE_CREATED":
            self.user_activity_log_service.sizes_created(audit_log_message)
        elif audit_log_message.type == "ORDER_CREATED":
            self.user_activity_log_service.order_created(audit_log_message)
        elif audit_log_message.type == "ORDER_UPDATED":
            self.user_activity_log_service.order_updated(audit_log_message)

    @staticmethod
    def __persist(audit_log_message: AuditLogMessage) -> None:
        db.session.add(
            AuditLog(
                id=audit_log_message.id,
                request=audit_log_message.request,
                type=audit_log_message.type,
                payload=audit_log_message.payload,
                diff=audit_log_message.diff,
                created_at=datetime.now(timezone.utc),
            )
        )

        db.session.commit()
