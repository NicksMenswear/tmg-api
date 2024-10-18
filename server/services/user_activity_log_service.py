import uuid

from server.database.database_manager import db
from server.database.models import UserActivityLog
from server.models.audit_model import AuditLogMessage


class UserActivityLogService:
    def __init__(self):
        pass

    def user_created(self, audit_log_message: AuditLogMessage):
        items = []

        if audit_log_message.payload.get("last_name") or audit_log_message.payload.get("first_name"):
            items.append(
                f"{audit_log_message.payload.get('first_name', '')} {audit_log_message.payload.get('last_name', '')}"
            )

        if audit_log_message.payload.get("email"):
            items.append(audit_log_message.payload.get("email"))

        if audit_log_message.payload.get("phone_number"):
            items.append(audit_log_message.payload.get("phone_number"))

        self.__persist(audit_log_message, "user_created", f"User created: {', '.join(items)}")

    def user_updated(self, audit_log_message: AuditLogMessage):
        diff = audit_log_message.get("diff")

        if "first_name" in diff or "last_name" in diff:
            old_first_name = diff.get("first_name", {}).get("before", audit_log_message.payload.get("first_name"))
            old_last_name = diff.get("last_name", {}).get("before", audit_log_message.payload.get("last_name"))
            new_first_name = diff.get("first_name", {}).get("after", audit_log_message.payload.get("first_name"))
            new_last_name = diff.get("last_name", {}).get("after", audit_log_message.payload.get("last_name"))

            self.__persist(
                audit_log_message,
                "user_name_updated",
                f'User name changed from "{old_first_name} {old_last_name}" to "{new_first_name} {new_last_name}"',
            )

        if "email" in diff:
            old_email = diff.get("email", {}).get("before", audit_log_message.payload.get("email"))
            new_email = diff.get("email", {}).get("after", audit_log_message.payload.get("email"))
            self.__persist(
                audit_log_message, "user_email_updated", f'User email changed from "{old_email}" to "{new_email}"'
            )

        if "phone_number" in diff:
            old_phone_number = diff.get("phone_number", {}).get("before", audit_log_message.payload.get("phone_number"))
            new_phone_number = diff.get("phone_number", {}).get("after", audit_log_message.payload.get("phone_number"))
            self.__persist(
                audit_log_message,
                "user_phone_number_updated",
                f"User phone number updated from {old_phone_number} to {new_phone_number}",
            )

        if "account_status" in diff:
            old_account_status = diff.get("account_status", {}).get(
                "before", audit_log_message.payload.get("account_status")
            )
            new_account_status = diff.get("account_status", {}).get(
                "after", audit_log_message.payload.get("account_status")
            )
            self.__persist(
                audit_log_message,
                "user_account_status_updated",
                f"User account status updated from {'ACTIVE' if old_account_status else 'INACTIVE'} to {'ACTIVE' if new_account_status else 'INACTIVE'}",
            )

        # if "meta" in diff:
        #     self.__persist(audit_log_message, "user_meta_updated", diff.get("meta"))

        if "shopify_id" in diff:
            self.__persist(
                audit_log_message,
                "user_shopify_account_associated",
                f"User associated with Shopify account with ID: {diff.get('after').get('shopify_id')}",
            )

    @staticmethod
    def __persist(audit_log_message: AuditLogMessage, handle: str, message: str) -> None:
        user_activity_log = UserActivityLog(
            user_id=audit_log_message.payload.get("id"),
            audit_log_id=uuid.UUID(audit_log_message.id),
            handle=handle,
            message=message,
        )
        db.session.save(user_activity_log)
        db.session.commit()
