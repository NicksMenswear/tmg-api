import random
import uuid
from datetime import datetime

from server.models.event_model import CreateEventModel, UpdateEventModel
from server.models.look_model import CreateLookModel, UpdateLookModel
from server.models.user_model import CreateUserModel, UpdateUserModel


def create_user_request(**user_data) -> CreateUserModel:
    return CreateUserModel(
        first_name=user_data.get("first_name", str(uuid.uuid4())),
        last_name=user_data.get("last_name", str(uuid.uuid4())),
        email=user_data.get("email", f"{str(uuid.uuid4())}@example.com"),
        account_status=user_data.get("account_status", True),
    )


def update_user_request(**user_data) -> UpdateUserModel:
    return UpdateUserModel(
        first_name=user_data.get("first_name", str(uuid.uuid4())),
        last_name=user_data.get("last_name", str(uuid.uuid4())),
    )


def create_event_request(**event_data) -> CreateEventModel:
    return CreateEventModel(
        event_name=event_data.get("event_name", str(uuid.uuid4())),
        event_date=event_data.get("event_date", datetime.now().isoformat()),
        user_id=event_data.get("user_id", uuid.uuid4()),
        is_active=event_data.get("is_active", True),
    )


def update_event_request(**event_data) -> UpdateEventModel:
    return UpdateEventModel(
        event_name=event_data.get("event_name", str(uuid.uuid4())),
        event_date=event_data.get("event_date", datetime.now().isoformat()),
    )


def create_look_request(**look_data) -> CreateLookModel:
    return CreateLookModel(
        look_name=look_data.get("look_name", str(uuid.uuid4())),
        user_id=look_data.get("user_id", uuid.uuid4()),
        product_specs=look_data.get("product_specs", {}),
    )


def update_look_request(**look_data) -> UpdateLookModel:
    return UpdateLookModel(
        look_name=look_data.get("look_name", str(uuid.uuid4())),
        product_specs=look_data.get("product_specs", {}),
    )


def role_request(**look_data):
    return {
        "role_name": look_data.get("role_name", str(uuid.uuid4())),
        "event_id": look_data.get("event_id", str(uuid.uuid4())),
    }


def attendee_request(**attendee_data):
    return {
        "email": attendee_data.get("email", f"{str(uuid.uuid4())}@example.com"),
        "event_id": attendee_data.get("event_id", str(uuid.uuid4())),
        "first_name": attendee_data.get("first_name", str(uuid.uuid4())),
        "last_name": attendee_data.get("last_name", str(uuid.uuid4())),
        "role": attendee_data.get("role"),
        "look_id": attendee_data.get("look_id"),
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


def create_cart_request(**cart_data):
    return {
        "user_id": cart_data.get("user_id"),
        "event_id": cart_data.get("event_id", str(uuid.uuid4())),
        "attendee_id": cart_data.get("attendee_id", str(uuid.uuid4())),
        "products": cart_data.get("products", []),
    }


def update_cart_request(**cart_data):
    return {
        "id": cart_data.get("id", str(uuid.uuid4())),
        "user_id": cart_data.get("user_id", str(uuid.uuid4())),
        "event_id": cart_data.get("event_id", str(uuid.uuid4())),
        "attendee_id": cart_data.get("attendee_id", str(uuid.uuid4())),
        "products": cart_data.get("products", []),
    }


def create_cart_product_request(**cart_product_data):
    return {
        "product_id": cart_product_data.get("product_id", random.randint(1000, 1000000)),
        "variation_id": cart_product_data.get("variation_id", random.randint(1000, 1000000)),
        "category": cart_product_data.get("category", str(uuid.uuid4())),
        "quantity": cart_product_data.get("quantity", random.randint(1, 100)),
    }


def create_groom_gift_discount_intent_request(**create_discount_intent):
    return {
        "attendee_id": create_discount_intent.get("attendee_id", str(uuid.uuid4())),
        "amount": create_discount_intent.get("amount", random.randint(10, 500)),
    }


def create_groom_full_pay_discount_intent_request(**create_discount_intent):
    return {
        "attendee_id": create_discount_intent.get("attendee_id", str(uuid.uuid4())),
        "pay_full": True,
    }


def shopify_paid_order_groom_gift_virtual_product_pay_for_discounts(sku="", customer_id=None, product_id=None):
    return {
        "id": random.randint(1000, 1000000),
        "discount_codes": [],
        "customer": {
            "id": customer_id if customer_id else random.randint(1000, 1000000),
            "email": "test@example.com",
        },
        "line_items": [
            {
                "id": product_id if product_id else random.randint(1000, 1000000),
                "sku": sku,
            }
        ],
    }


def shopify_paid_order_user_pays_for_order_with_discounts(discounts):
    return {
        "id": random.randint(1000, 1000000),
        "discount_codes": [{"code": discount} for discount in discounts],
        "line_items": [
            {
                "id": random.randint(1000, 1000000),
                "sku": "PRODUCT_SKU",
            }
        ],
    }


def apply_discounts_request(**apply_discounts_data):
    return {
        "event_id": apply_discounts_data.get("event_id", str(uuid.uuid4())),
        "shopify_cart_id": apply_discounts_data.get("shopify_cart_id", str(uuid.uuid4())),
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
