import json
import logging
from datetime import datetime, timezone

from flask import request
from sqlalchemy import event

from server.database.database_manager import db
from server.database.models import (
    User,
    Event,
    Attendee,
    Look,
    Order,
    OrderItem,
    Product,
    Discount,
    Size,
    Measurement,
    Address,
    AuditLog,
)
from server.flask_app import FlaskApp
from server.logs import audit
from server.models.audit_model import AuditLogMessage
from server.services import ServiceError

logger = logging.getLogger(__name__)


class AuditLogService:
    @classmethod
    def init_audit_logging(cls):
        entities = [User, Event, Attendee, Look, Order, OrderItem, Product, Discount, Size, Measurement, Address]

        for entity in entities:
            log_prefix = f"{entity.__name__.upper()}"

            event.listen(
                entity,
                "after_insert",
                lambda m, c, t, lp=log_prefix: cls.__log_operation(t, f"{lp}_CREATED"),
            )
            event.listen(
                entity,
                "after_update",
                lambda m, c, t, lp=log_prefix: cls.__log_operation(t, f"{lp}_UPDATED"),
            )
            event.listen(
                entity,
                "before_delete",
                lambda m, c, t, lp=log_prefix: cls.__log_operation(t, f"{lp}_DELETED"),
            )

    @classmethod
    def __log_operation(cls, target, operation):
        if not FlaskApp.current():
            return

        try:
            serializable_request = cls.__request_to_dict()
            serializable_payload = target.serialize()

            FlaskApp.current().aws_service.enqueue_message(
                FlaskApp.current().audit_log_sqs_queue_url,
                AuditLogMessage(type=operation, request=serializable_request, payload=serializable_payload).to_string(),
            )
        except Exception as e:
            logger.exception(f"Failed to enqueue audit log message: {e}")

    @classmethod
    def __request_to_dict(cls) -> dict:
        # if no request or default request
        if not request or (
            request.method == "GET" and request.path == "/" and not request.query_string and not request.data
        ):
            return {}

        query_string = request.query_string.decode("utf-8") if request.query_string else ""
        items = query_string.split("&")
        loggable_items = {}

        for item in items:
            if not item:
                continue

            key, value = item.split("=")

            if key in {"path_prefix", "shop", "timestamp", "signature"}:
                continue

            loggable_items[key] = value

        data = request.data.decode("utf-8")
        json_data = {}

        if data:
            json_data = json.loads(data)

            # do not send serialized image base64 into audit log queue - too big
            if "image" in json_data:
                json_data["image"] = "<skipped>"

        return {
            "method": request.method,
            "path": request.path,
            "qs": loggable_items,
            "data": json_data,
        }

    @staticmethod
    def save_audit_log(audit_log_message: AuditLogMessage):
        try:
            audit_log = AuditLog()
            audit_log.request = audit_log_message.request
            audit_log.type = audit_log_message.type
            audit_log.payload = audit_log_message.payload
            audit_log.created_at = datetime.now(timezone.utc)

            db.session.add(audit_log)
            db.session.commit()
        except Exception as e:
            raise ServiceError(f"Error saving audit log: {e}")
