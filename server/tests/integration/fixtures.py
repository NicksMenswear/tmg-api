import base64
import random
import uuid
from datetime import datetime, timedelta

from server.models.attendee_model import CreateAttendeeModel, UpdateAttendeeModel
from server.models.discount_model import (
    ApplyDiscountModel,
    CreateDiscountIntentAmount,
    CreateDiscountIntentPayFull,
)
from server.models.event_model import CreateEventModel, UpdateEventModel, EventTypeModel
from server.models.look_model import CreateLookModel, UpdateLookModel
from server.models.role_model import CreateRoleModel, UpdateRoleModel
from server.models.user_model import CreateUserModel, UpdateUserModel
from server.tests import utils


def create_user_request(**user_data) -> CreateUserModel:
    return CreateUserModel(
        first_name=user_data.get("first_name", utils.generate_unique_name()),
        last_name=user_data.get("last_name", utils.generate_unique_name()),
        email=user_data.get("email", utils.generate_email()),
        account_status=user_data.get("account_status", True),
        phone_number=user_data.get("phone_number", None),
        shopify_id=user_data.get("shopify_id", None),
    )


def update_user_request(**user_data) -> UpdateUserModel:
    return UpdateUserModel(
        first_name=user_data.get("first_name", utils.generate_unique_name()),
        last_name=user_data.get("last_name", utils.generate_unique_name()),
    )


def create_event_request(**create_event) -> CreateEventModel:
    return CreateEventModel(
        name=create_event.get("name", str(uuid.uuid4())),
        event_at=create_event.get("event_at", (datetime.now() + timedelta(weeks=10)).isoformat()),
        user_id=create_event.get("user_id", uuid.uuid4()),
        is_active=create_event.get("is_active", True),
        type=create_event.get("type", EventTypeModel.OTHER),
    )


def update_event_request(**update_event) -> UpdateEventModel:
    return UpdateEventModel(
        name=update_event.get("name", str(uuid.uuid4())),
        event_at=update_event.get("event_at", datetime.now().isoformat()),
    )


def create_look_request(**look_data) -> CreateLookModel:
    return CreateLookModel(
        name=look_data.get("name", str(uuid.uuid4())),
        user_id=look_data.get("user_id", uuid.uuid4()),
        product_specs=look_data.get("product_specs", {}),
        is_active=look_data.get("is_active", True),
        image=look_data.get("image"),
    )


def update_look_request(**look_data) -> UpdateLookModel:
    return UpdateLookModel(
        name=look_data.get("name", str(uuid.uuid4())),
        product_specs=look_data.get("product_specs", {}),
    )


def create_role_request(**role_data):
    return CreateRoleModel(
        name=role_data.get("name", str(uuid.uuid4())),
        event_id=role_data.get("event_id", uuid.uuid4()),
        is_active=role_data.get("is_active", True),
    )


def update_role_request(**role_data):
    return UpdateRoleModel(
        name=role_data.get("name", str(uuid.uuid4())),
    )


def create_attendee_request(**attendee_data):
    return CreateAttendeeModel(
        email=attendee_data.get("email", utils.generate_email()),
        first_name=attendee_data.get("first_name", utils.generate_unique_name()),
        last_name=attendee_data.get("last_name", utils.generate_unique_name()),
        event_id=attendee_data.get("event_id", uuid.uuid4()),
        role_id=attendee_data.get("role_id"),
        look_id=attendee_data.get("look_id"),
        is_active=attendee_data.get("is_active", True),
    )


def update_attendee_request(**attendee_data):
    return UpdateAttendeeModel(
        event_id=attendee_data.get("event_id", uuid.uuid4()),
        role_id=attendee_data.get("role_id"),
        look_id=attendee_data.get("look_id"),
        is_active=attendee_data.get("is_active", True),
    )


def create_gift_discount_intent_request(**create_discount_intent):
    return CreateDiscountIntentAmount(
        attendee_id=create_discount_intent.get("attendee_id", str(uuid.uuid4())),
        amount=create_discount_intent.get("amount", random.randint(10, 500)),
    )


def create_full_pay_discount_intent_request(**create_discount_intent):
    return CreateDiscountIntentPayFull(
        attendee_id=create_discount_intent.get("attendee_id", str(uuid.uuid4())),
        pay_full=True,
    )


def webhook_shopify_line_item(product_id=None, variant_id=None, sku=""):
    return {
        "id": random.randint(1000, 1000000),
        "product_id": product_id if product_id else random.randint(1000, 1000000),
        "variant_id": variant_id if variant_id else random.randint(1000, 1000000),
        "sku": sku,
        "name": f"product-{utils.generate_unique_string()}",
        "price": random.randint(10, 100),
        "quantity": random.randint(1, 5),
    }


def webhook_shopify_paid_order(customer_email=None, customer_id=None, discounts=None, line_items=None, event_id=None):
    order = {
        "id": random.randint(1000, 1000000),
        "discount_codes": [] if not discounts else [{"code": discount} for discount in discounts],
        "customer": {
            "id": customer_id if customer_id else random.randint(1000, 1000000),
            "email": customer_email if customer_email else "test@example.com",
        },
        "order_number": random.randint(1000, 1000000),
        "created_at": datetime.now().isoformat(),
        "shipping_address": {
            "address1": "123 Shipping Address",
            "city": "City",
            "province": "Province",
            "zip": "12345",
            "country": "US",
        },
        "line_items": [] if not line_items else line_items,
    }

    if event_id:
        order["note_attributes"] = [{"name": "__event_id", "value": event_id}]

    return order


def webhook_customer_update(
    shopify_id=None, email: str = None, first_name=None, last_name=None, account_status=True, phone=None
):
    return {
        "id": shopify_id if shopify_id else random.randint(1000, 1000000),
        "email": email if email else utils.generate_email(),
        "first_name": first_name if first_name else utils.generate_unique_name(),
        "last_name": last_name if last_name else utils.generate_unique_name(),
        "state": "enabled" if account_status else "disabled",
        "phone": phone if phone else "",
    }


def apply_discounts_request(**apply_discounts_data):
    return ApplyDiscountModel(
        event_id=apply_discounts_data.get("event_id", uuid.uuid4()),
        shopify_cart_id=apply_discounts_data.get("shopify_cart_id", str(uuid.uuid4())),
    )


######################
# LEGACY FIXTURES
######################


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


def get_look_1_image_in_b64():
    return file_to_b64("assets/look_1.png")


def get_look_2_image_in_b64():
    return file_to_b64("assets/look_2.png")


def file_to_b64(file_path):
    with open(file_path, "rb") as file:
        content = file.read()

    return base64.b64encode(content).decode("utf-8")


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


def store_size_request(**data) -> dict:
    return {
        "user_id": uuid.uuid4(),
        "data": {"test": 123},
    }
