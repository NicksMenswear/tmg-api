import json
import logging
import uuid
from typing import Dict, Any

from flask import request
from sqlalchemy import event
from sqlalchemy.orm.attributes import get_history

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
    SerializableMixin,
)
from server.flask_app import FlaskApp
from server.models.audit_log_model import AuditLogMessage

logger = logging.getLogger(__name__)


def init_audit_logging():
    if not FlaskApp.current():
        return

    entities = [User, Event, Attendee, Look, Order, OrderItem, Product, Discount, Size, Measurement, Address]

    for entity in entities:
        log_prefix = entity.__name__.upper()

        event.listen(
            entity,
            "after_insert",
            lambda m, c, t, lp=log_prefix: _log_operation(t, f"{lp}_CREATED", False),
        )
        event.listen(
            entity,
            "after_update",
            lambda m, c, t, lp=log_prefix: _log_operation(t, f"{lp}_UPDATED", True),
        )
        event.listen(
            entity,
            "before_delete",
            lambda m, c, t, lp=log_prefix: _log_operation(t, f"{lp}_DELETED", False),
        )


def _log_operation(target, operation, include_diff=False):
    try:
        serializable_request = _request_to_dict()
        serializable_payload = target.serialize()

        if include_diff:
            diff: Dict[str, Any] = _build_diff(target)

            if not diff:
                return

            _send_message(
                AuditLogMessage(
                    id=str(uuid.uuid4()),
                    type=operation,
                    request=serializable_request,
                    payload=serializable_payload,
                    diff=diff,
                )
            )
        else:
            _send_message(
                AuditLogMessage(
                    id=str(uuid.uuid4()),
                    type=operation,
                    request=serializable_request,
                    payload=serializable_payload,
                    diff=None,
                )
            )
    except Exception as e:
        logger.exception(f"Failed to enqueue audit log message: {e}")


def _build_diff(target):
    diff = {}

    after_state = {attr.key: getattr(target, attr.key) for attr in target.__table__.columns}

    before_state = {}
    for attr in target.__table__.columns:
        if attr.key in {"updated_at"}:
            continue

        history = get_history(target, attr.key)

        if history.has_changes():
            before_state[attr.key] = history.deleted[0] if history.deleted else None
            diff[attr.key] = {
                "before": SerializableMixin.normalize(before_state[attr.key]),
                "after": SerializableMixin.normalize(after_state[attr.key]),
            }

    return diff


def _request_to_dict() -> dict:
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

        if key in {"path_prefix", "shop", "signature"}:
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


def _is_in_test_mode() -> bool:
    return FlaskApp.current().config["TMG_APP_TESTING"]


def _send_message(audit_log_message: AuditLogMessage) -> None:
    app = FlaskApp.current()

    try:
        if _is_in_test_mode():
            audit_log_service = app.audit_log_service
            audit_log_service.process(audit_log_message)
        else:
            aws_service = app.aws_service
            aws_service.enqueue_message(app.audit_log_sqs_queue_url, audit_log_message.to_string())
    except Exception as e:
        logger.exception(f"Failed to send audit log message: {e}")
