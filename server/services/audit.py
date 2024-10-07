import json

from flask import request
from sqlalchemy import event

from server.database.database_manager import db
from server.database.models import (
    AuditLog,
    User,
    Event,
    Attendee,
    Look,
    Role,
    Order,
    OrderItem,
    Product,
    Discount,
    Size,
    Measurement,
    Address,
)


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
    audit_log = AuditLog()
    audit_log.request = __request_to_dict()
    audit_log.type = operation
    audit_log.payload = target.serialize()
    db.session.add(audit_log)


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
