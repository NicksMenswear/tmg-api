import random
import uuid
from datetime import datetime


def user_request(**user_data):
    return {
        "first_name": user_data.get("first_name", str(uuid.uuid4())),
        "last_name": user_data.get("last_name", str(uuid.uuid4())),
        "email": user_data.get("email", f"{str(uuid.uuid4())}@example.com"),
        "account_status": user_data.get("account_status", True),
    }


def product_request(**product_data):
    return {
        "name": product_data.get("name", str(uuid.uuid4())),
        "Active": product_data.get("is_active", True),
        "SKU": product_data.get("sku", str(uuid.uuid4())),
        "Weight": product_data.get("weight", 1.0),
        "Height": product_data.get("height", 1.0),
        "Width": product_data.get("width", 1.0),
        "Length": product_data.get("length", 1.0),
        "Value": product_data.get("value", 1.0),
        "Price": product_data.get("price", 1.0),
        "On_hand": product_data.get("on_hand", 1),
        "Allocated": product_data.get("allocated", 1),
        "Reserve": product_data.get("reserve", 1),
        "Non_sellable_total": product_data.get("non_sellable_total", 1),
        "Reorder_level": product_data.get("reorder_level", 1),
        "Reorder_amount": product_data.get("reorder_amount", 1),
        "Replenishment_level": product_data.get("replenishment_level", 1),
        "Available": product_data.get("available", 1),
        "Backorder": product_data.get("backorder", 1),
        "Barcode": product_data.get("barcode", random.randint(1000, 100000)),
        "Tags": product_data.get("tags", ["tag1", "tag2"]),
    }


def event_request(**event_data):
    return {
        "event_name": event_data.get("event_name", str(uuid.uuid4())),
        "event_date": event_data.get("event_date", datetime.now().isoformat()),
        "user_id": event_data.get("user_id", str(uuid.uuid4())),
        "is_active": event_data.get("is_active", True),
    }


def look_request(**look_data):
    return {
        "look_name": look_data.get("look_name", str(uuid.uuid4())),
        "user_id": look_data.get("user_id", str(uuid.uuid4())),
        "event_id": look_data.get("event_id", None),
        "product_specs": look_data.get("product_specs", {}),
        "product_final_image": look_data.get("product_final_image", ""),
    }


def update_look_request(**look_data):
    return {
        "look_id": look_data.get("look_id", str(uuid.uuid4())),
        "look_name": look_data.get("look_name", str(uuid.uuid4())),
        "user_id": look_data.get("user_id", str(uuid.uuid4())),
        "email": look_data.get("email", f"{str(uuid.uuid4())}@example.com"),
        "attendee_id": look_data.get("attendee_id", str(uuid.uuid4())),
        "event_id": look_data.get("event_id", None),
        "flag": look_data.get("flag", False),
        "product_specs": look_data.get("product_specs", {}),
        "product_final_image": look_data.get("product_final_image", ""),
    }


def role_request(**look_data):
    return {
        "role_name": look_data.get("role_name", str(uuid.uuid4())),
        "event_id": look_data.get("event_id", str(uuid.uuid4())),
        "look_id": look_data.get("look_id", str(uuid.uuid4())),
    }


def attendee_request(**attendee_data):
    return {
        "email": attendee_data.get("email", f"{str(uuid.uuid4())}@example.com"),
        "event_id": attendee_data.get("event_id", str(uuid.uuid4())),
        "first_name": attendee_data.get("first_name", str(uuid.uuid4())),
        "last_name": attendee_data.get("last_name", str(uuid.uuid4())),
        "role": attendee_data.get("role"),
        "style": attendee_data.get("style", random.randint(1, 100)),
        "invite": attendee_data.get("invite", random.randint(1, 100)),
        "pay": attendee_data.get("pay", random.randint(1, 100)),
        "size": attendee_data.get("size", random.randint(1, 100)),
        "ship": attendee_data.get("ship", random.randint(1, 100)),
        "is_active": attendee_data.get("is_active", True),
    }


def order_request(**order_data):
    return {
        "email": order_data.get("email", f"{str(uuid.uuid4())}@example.com"),
        "user_id": order_data.get("user_id", str(uuid.uuid4())),
        "event_id": order_data.get("event_id", str(uuid.uuid4())),
        "shipped_date": order_data.get("shipped_date", datetime.now().isoformat()),
        "received_date": order_data.get("received_date", datetime.now().isoformat()),
        "items": order_data.get("items", []),
    }


def order_item(**order_item_data):
    return {
        "name": order_item_data.get("name", str(uuid.uuid4())),
        "quantity": order_item_data.get("quantity", random.randint(1, 100)),
    }


def update_order_request(**order_data):
    return {
        "id": order_data.get("id", str(uuid.uuid4())),
        "shipped_date": order_data.get("shipped_date", datetime.now().isoformat()),
        "received_date": order_data.get("received_date", datetime.now().isoformat()),
    }
