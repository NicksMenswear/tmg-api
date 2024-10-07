import json
import logging

from flask import request
from sqlalchemy import event

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
)
from server.flask_app import FlaskApp
from server.models.audit_model import AuditLogMessage

logger = logging.getLogger(__name__)


def init_audit_logging():
    entities = [User, Event, Attendee, Look, Order, OrderItem, Product, Discount, Size, Measurement, Address]

    for entity in entities:
        log_prefix = f"{entity.__name__.upper()}"

        event.listen(
            entity,
            "after_insert",
            lambda m, c, t, lp=log_prefix: __log_operation(t, f"{lp}_CREATED"),
        )
        event.listen(
            entity,
            "after_update",
            lambda m, c, t, lp=log_prefix: __log_operation(t, f"{lp}_UPDATED"),
        )
        event.listen(
            entity,
            "before_delete",
            lambda m, c, t, lp=log_prefix: __log_operation(t, f"{lp}_DELETED"),
        )


def __log_operation(target, operation):
    serializable_request = __request_to_dict()
    serializable_payload = target.serialize()

    if not FlaskApp.current():
        return

        try:
            FlaskApp.current().aws_service.enqueue_message(
                FlaskApp.current().audit_log_sqs_queue_url,
                AuditLogMessage(type=operation, request=serializable_request, payload=serializable_payload).to_string(),
            )
        except Exception as e:
            logger.exception(f"Failed to enqueue audit log message: {e}")


def __request_to_dict() -> dict:
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

    return {
        "method": request.method,
        "path": request.path,
        "qs": loggable_items,
        "data": json_data,
    }
