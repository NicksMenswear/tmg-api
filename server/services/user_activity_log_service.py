from datetime import datetime
from uuid import UUID

from server.database.database_manager import db
from server.database.models import UserActivityLog
from server.models.audit_log_model import AuditLogMessage
from server.services.event_service import EventService
from server.services.integrations.activecampaign_service import logger
from server.services.user_service import UserService


class UserActivityLogService:
    def __init__(self, user_service: UserService, event_service: EventService):
        self.__user_service = user_service
        self.__event_service = event_service

    def user_created(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload
        user_id = data["id"]
        audit_log_id = audit_log_message.id

        items = []

        if data.get("last_name") or data.get("first_name"):
            items.append(f"{data.get('first_name', '')} {data.get('last_name', '')}")

        if data.get("email"):
            items.append(data.get("email"))

        if data.get("phone_number"):
            items.append(data.get("phone_number"))

        self.__persist(user_id, audit_log_id, "user_created", f"User created: {', '.join(items)}")

    def user_updated(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload
        user_id = data.get("id")
        audit_log_id = audit_log_message.id
        diff = audit_log_message.diff

        if "first_name" in diff or "last_name" in diff:
            old_first_name = diff["first_name"].get("before", data.get("first_name"))
            old_last_name = diff["last_name"].get("before", data.get("last_name"))
            new_first_name = diff["first_name"].get("after", data.get("first_name"))
            new_last_name = diff["last_name"].get("after", data.get("last_name"))

            self.__persist(
                user_id,
                audit_log_id,
                "user_name_updated",
                f'Name changed from "{old_first_name} {old_last_name}" to "{new_first_name} {new_last_name}"',
            )

        if "email" in diff:
            old_email = diff["email"]["before"]
            new_email = diff["email"]["after"]

            self.__persist(
                user_id, audit_log_id, "user_email_updated", f'User email changed from "{old_email}" to "{new_email}"'
            )

        if "phone_number" in diff:
            old_phone_number = diff["phone_number"]["before"]
            new_phone_number = diff["phone_number"]["after"]

            self.__persist(
                user_id,
                audit_log_id,
                "user_phone_number_updated",
                f"User phone number updated from {old_phone_number} to {new_phone_number}",
            )

        if "account_status" in diff:
            old_account_status = diff["account_status"]["before"]
            new_account_status = diff["account_status"]["after"]

            self.__persist(
                user_id,
                audit_log_id,
                "user_account_status_updated",
                f"User account status updated from {'ACTIVE' if old_account_status else 'INACTIVE'} to {'ACTIVE' if new_account_status else 'INACTIVE'}",
            )

        if "shopify_id" in diff:
            new_shopify_id = diff["shopify_id"]["after"]

            self.__persist(
                user_id,
                audit_log_id,
                "user_shopify_account_associated",
                f"User associated with Shopify account with ID: {new_shopify_id}",
            )

    def event_created(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload
        event = self.__event_service.get_event_by_id(data["id"])

        event_name = data["name"]
        event_date = datetime.fromisoformat(data["event_at"]).strftime("%d %b %Y")
        event_type = data["type"]

        self.__persist(
            str(event.user_id),
            audit_log_message.id,
            "event_created",
            f"Event created {event_type}, {event_name}, {event_date}",
        )

    def event_updated(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload
        diff = audit_log_message.diff

        event = self.__event_service.get_event_by_id(data["id"])

        if "name" in diff:
            old_name = diff["name"]["before"]
            new_name = diff["name"]["after"]

            self.__persist(
                str(event.user_id),
                audit_log_message.id,
                "event_name_updated",
                f'Event name changed from "{old_name}" to "{new_name}"',
            )

        if "event_at" in diff:
            old_date = datetime.fromisoformat(diff["event_at"]["before"]).strftime("%d %b %Y")
            new_date = datetime.fromisoformat(diff["event_at"]["after"]).strftime("%d %b %Y")

            self.__persist(
                str(event.user_id),
                audit_log_message.id,
                "event_date_updated",
                f'Event date changed from "{old_date}" to "{new_date}"',
            )

        if "is_active" in diff and not diff["is_active"]["after"]:
            self.__persist(
                str(event.user_id),
                audit_log_message.id,
                "event_deleted",
                f'Event "{data["name"]}" deleted',
            )

    @staticmethod
    def __persist(user_id: str, audit_log_id: UUID, handle: str, message: str) -> None:
        try:
            user_activity_log = UserActivityLog(
                user_id=UUID(user_id),
                audit_log_id=audit_log_id,
                handle=handle,
                message=message,
            )
            db.session.add(user_activity_log)
            db.session.commit()
        except Exception as e:
            logger.exception(f"Error persisting user activity log message: {audit_log_id}")
            db.session.rollback()
