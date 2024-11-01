import logging
from datetime import datetime, timezone

from server.database.database_manager import db
from server.database.models import AuditLog
from server.models.audit_log_model import AuditLogMessage
from server.services.tagging_service import TaggingService
from server.services.user_activity_log_service import UserActivityLogService

logger = logging.getLogger(__name__)


class AuditLogService:
    def __init__(self, tagging_service: TaggingService, user_activity_log_service: UserActivityLogService):
        self.__tagging_service = tagging_service
        self.__user_activity_log_service = user_activity_log_service

    def process(self, audit_log_message: AuditLogMessage) -> None:
        self.__persist(audit_log_message)

        logger.info(f"Processing '{audit_log_message.type}' message for '{audit_log_message.payload.get('id')}'")

        if audit_log_message.type == "USER_CREATED":
            self.__user_activity_log_service.user_created(audit_log_message)
        elif audit_log_message.type == "USER_UPDATED":
            self.__user_activity_log_service.user_updated(audit_log_message)
        elif audit_log_message.type == "EVENT_CREATED":
            self.__user_activity_log_service.event_created(audit_log_message)
        elif audit_log_message.type == "EVENT_UPDATED":
            self.__user_activity_log_service.event_updated(audit_log_message)
            self.__tagging_service.tag_customers_on_event_updated(audit_log_message)
            self.__tagging_service.tag_products_on_event_updated(audit_log_message)
        elif audit_log_message.type == "ATTENDEE_CREATED":
            self.__user_activity_log_service.attendee_created(audit_log_message)
        elif audit_log_message.type == "ATTENDEE_UPDATED":
            self.__user_activity_log_service.attendee_updated(audit_log_message)
            self.__tagging_service.tag_customers_on_attendee_updated(audit_log_message)
            self.__tagging_service.tag_products_on_attendee_updated(audit_log_message)
        elif audit_log_message.type == "LOOK_CREATED":
            self.__user_activity_log_service.look_created(audit_log_message)
        elif audit_log_message.type == "LOOK_UPDATED":
            self.__user_activity_log_service.look_updated(audit_log_message)
        elif audit_log_message.type == "MEASUREMENT_CREATED":
            self.__user_activity_log_service.measurements_created(audit_log_message)
        elif audit_log_message.type == "SIZE_CREATED":
            self.__user_activity_log_service.sizes_created(audit_log_message)
        elif audit_log_message.type == "ORDER_CREATED":
            self.__user_activity_log_service.order_created(audit_log_message)
        elif audit_log_message.type == "ORDER_UPDATED":
            self.__user_activity_log_service.order_updated(audit_log_message)

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
