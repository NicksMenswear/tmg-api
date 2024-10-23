from datetime import datetime
from uuid import UUID

from server.database.database_manager import db
from server.database.models import UserActivityLog
from server.models.audit_log_model import AuditLogMessage
from server.services.attendee_service import AttendeeService
from server.services.event_service import EventService
from server.services.look_service import LookService
from server.services.order_service import OrderService
from server.services.role_service import RoleService
from server.services.user_service import UserService


class UserActivityLogService:
    def __init__(
        self,
        user_service: UserService,
        event_service: EventService,
        attendee_service: AttendeeService,
        role_service: RoleService,
        look_service: LookService,
        order_service: OrderService,
    ):
        self.__user_service = user_service
        self.__event_service = event_service
        self.__attendee_service = attendee_service
        self.__role_service = role_service
        self.__look_service = look_service
        self.__order_service = order_service

    def user_created(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload
        user_id = UUID(data["id"])
        audit_log_id = UUID(audit_log_message.id)

        items = []

        if data.get("last_name") or data.get("first_name"):
            items.append(f"{data.get('first_name', '')} {data.get('last_name', '')}")

        if data.get("email"):
            items.append(data.get("email"))

        if data.get("phone_number"):
            items.append(data.get("phone_number"))

        self.__persist(
            user_id,
            audit_log_id,
            "user_created",
            f"User created: {', '.join(items)}",
        )

    def user_updated(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload
        user_id = UUID(data.get("id"))
        audit_log_id = UUID(audit_log_message.id)
        diff = audit_log_message.diff

        if "first_name" in diff or "last_name" in diff:
            old_first_name = diff.get("first_name", {}).get("before", data.get("first_name"))
            old_last_name = diff.get("last_name", {}).get("before", data.get("last_name"))
            new_first_name = diff.get("first_name", {}).get("after", data.get("first_name"))
            new_last_name = diff.get("last_name", {}).get("after", data.get("last_name"))

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
                user_id,
                audit_log_id,
                "user_email_updated",
                f'User email changed from "{old_email}" to "{new_email}"',
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
        audit_log_id = UUID(audit_log_message.id)

        event_name = data["name"]
        event_date = datetime.fromisoformat(data["event_at"]).strftime("%d %b %Y") if data["event_at"] else None
        event_type = data["type"]

        self.__persist(
            event.user_id,
            audit_log_id,
            "event_created",
            f"Event created: {event_type}, {event_name}, {event_date}",
        )

    def event_updated(self, audit_log_message: AuditLogMessage):
        diff = audit_log_message.diff

        if not diff:
            return

        data = audit_log_message.payload
        audit_log_id = UUID(audit_log_message.id)
        event = self.__event_service.get_event_by_id(data["id"])

        if "name" in diff:
            old_name = diff["name"]["before"]
            new_name = diff["name"]["after"]

            self.__persist(
                event.user_id,
                audit_log_id,
                "event_name_updated",
                f'Event name changed from "{old_name}" to "{new_name}"',
            )

        if "event_at" in diff:
            old_date = (
                datetime.fromisoformat(diff["event_at"]["before"]).strftime("%d %b %Y")
                if diff["event_at"]["before"]
                else None
            )
            new_date = (
                datetime.fromisoformat(diff["event_at"]["after"]).strftime("%d %b %Y")
                if diff["event_at"]["before"]
                else None
            )

            self.__persist(
                event.user_id,
                audit_log_id,
                "event_date_updated",
                f'Event date changed from "{old_date}" to "{new_date}"',
            )

        if "is_active" in diff and not diff["is_active"]["after"]:
            self.__persist(
                event.user_id,
                audit_log_id,
                "event_deleted",
                f'Event "{data["name"]}" deleted',
            )

    def attendee_created(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload

        event_id = data.get("event_id")
        event = self.__event_service.get_event_by_id(event_id)
        attendee_email = data.get("email")
        audit_log_id = UUID(audit_log_message.id)

        attendee_name = f'{data.get("first_name")} {data.get("last_name")}'
        attendee_email = attendee_email if attendee_email else "email not provided"

        self.__persist(
            event.user_id,
            audit_log_id,
            "attendee_created",
            f'Attendee added to event "{event.name}": {attendee_name}, {attendee_email}',
        )

    def attendee_updated(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload
        diff = audit_log_message.diff
        audit_log_id = UUID(audit_log_message.id)

        if not diff:
            return

        event_id: UUID = UUID(data.get("event_id"))
        attendee_id: UUID = UUID(data.get("id"))
        event = self.__event_service.get_event_by_id(event_id)

        if "is_active" in diff:
            attendee = self.__attendee_service.get_attendee_by_id(attendee_id, False)

            self.__persist(
                event.user_id,
                audit_log_id,
                "attendee_deleted",
                f'Attendee "{attendee.first_name} {attendee.last_name}" has been removed from event "{event.name}"',
            )

            return

        attendee = self.__attendee_service.get_attendee_by_id(attendee_id, False)
        attendee_name = f"{attendee.first_name} {attendee.last_name}"

        if "first_name" in diff or "last_name" in diff:
            old_first_name = diff["first_name"].get("before", data.get("first_name"))
            old_last_name = diff["last_name"].get("before", data.get("last_name"))
            new_first_name = diff["first_name"].get("after", data.get("first_name"))
            new_last_name = diff["last_name"].get("after", data.get("last_name"))

            self.__persist(
                event.user_id,
                audit_log_id,
                "attendee_name_updated",
                f'Attendee name changed from "{old_first_name} {old_last_name}" to "{new_first_name} {new_last_name}"',
            )

        if "email" in diff:
            old_email = diff["email"]["before"]
            new_email = diff["email"]["after"]

            if not old_email:
                message = f'Email for attendee "{attendee_name}" was set to "{new_email}"'
            else:
                message = f'Attendee "{attendee_name}" email has been update from "{old_email}" to "{new_email}"'

            self.__persist(
                event.user_id,
                audit_log_id,
                "attendee_email_updated",
                message,
            )

        if "role_id" in diff:
            old_role_id = diff["role_id"]["before"]
            new_role_id = diff["role_id"]["after"]

            new_role = self.__role_service.get_role_by_id(new_role_id)

            if not old_role_id:
                message = f'Attendee role was set to "{new_role.name}"'
            else:
                old_role = self.__role_service.get_role_by_id(old_role_id)
                message = f'Attendee role was updated from "{old_role.name}" to "{new_role.name}"'

            self.__persist(
                event.user_id,
                audit_log_id,
                "attendee_role_updated",
                message,
            )

        if "look_id" in diff:
            old_look_id = diff["look_id"]["before"]
            new_look_id = diff["look_id"]["after"]

            new_look = self.__look_service.get_look_by_id(new_look_id)

            if not old_look_id:
                message = f'Attendee look was set to "{new_look.name}"'
            else:
                old_look = self.__look_service.get_look_by_id(old_look_id)
                message = f'Attendee look was updated from "{old_look.name}" to "{new_look.name}"'

            self.__persist(
                event.user_id,
                audit_log_id,
                "attendee_look_updated",
                message,
            )

        if "invite" in diff:
            self.__persist(
                event.user_id,
                audit_log_id,
                "attendee_was_invited_to_event",
                message=f'Attendee "{attendee_name}" has been invited to event {event.name}',
            )

        if "pay" in diff:
            self.__persist(
                event.user_id,
                audit_log_id,
                "attendee_was_invited_to_event",
                message=f'Attendee "{attendee_name}" paid for a suit in {event.name}',
            )

    def look_created(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload

        user_id = UUID(data.get("user_id"))
        audit_log_id = UUID(audit_log_message.id)
        look_name = data.get("name")

        self.__persist(
            user_id,
            audit_log_id,
            "look_created",
            f'Created look "{look_name}"',
        )

    def look_updated(self, audit_log_message: AuditLogMessage):
        diff = audit_log_message.diff

        if not diff:
            return

        data = audit_log_message.payload
        audit_log_id = UUID(audit_log_message.id)
        user_id = UUID(data.get("user_id"))
        look_id = UUID(data.get("id"))

        look = self.__look_service.get_look_by_id(look_id)

        if "is_active" in diff:
            self.__persist(
                user_id,
                audit_log_id,
                "look_deleted",
                f'Look "{look.name}" has been removed',
            )

    def measurements_created(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload

        user_id = UUID(data.get("user_id"))
        audit_log_id = UUID(audit_log_message.id)

        self.__persist(
            user_id,
            audit_log_id,
            "measurements_provided",
            f"Provided new measurements",
        )

    def sizes_created(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload

        user_id = UUID(data.get("user_id"))
        audit_log_id = UUID(audit_log_message.id)

        self.__persist(
            user_id,
            audit_log_id,
            "sizes_recalculated",
            f"Sizes calculated",
        )

    def order_created(self, audit_log_message: AuditLogMessage):
        data = audit_log_message.payload

        user_id = UUID(data.get("user_id"))
        audit_log_id = UUID(audit_log_message.id)
        order_id = UUID(data.get("id"))

        order = self.__order_service.get_order_by_id(order_id)

        self.__persist(
            user_id,
            audit_log_id,
            "order_placed",
            f"Order placed {order.order_number}, {order.shipping_method}, {order.status}",
        )

    def order_updated(self, audit_log_message: AuditLogMessage):
        diff = audit_log_message.diff

        if not diff:
            return

        data = audit_log_message.payload
        user_id = UUID(data.get("user_id"))
        audit_log_id = UUID(audit_log_message.id)

        if "status" in diff:
            old_status = diff["status"]["before"]
            new_status = diff["status"]["after"]

            self.__persist(
                user_id,
                audit_log_id,
                "order_status_updated",
                f'Order status updated from "{old_status}" to "{new_status}"',
            )

    @staticmethod
    def __persist(user_id: UUID, audit_log_id: UUID, handle: str, message: str) -> None:
        user_activity_log = UserActivityLog(
            user_id=user_id,
            audit_log_id=audit_log_id,
            handle=handle,
            message=message,
        )
        db.session.add(user_activity_log)
        db.session.commit()
