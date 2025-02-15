import enum
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
    Enum,
    text,
    ARRAY,
    JSON,
    BigInteger,
    Index,
    inspect,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

if os.getenv("USE_FLASK") == "false":
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()
else:
    from server.database.database_manager import db

    Base = db.Model


@enum.unique
class ActivityType(enum.Enum):
    USER_UPDATE = "user_update"
    EVENT_UPDATE = "event_update"
    ORDER_UPDATE = "order_update"
    RMA_UPDATE = "rma_update"


@enum.unique
class SourceType(enum.Enum):
    NM = "NM"
    TMG = "TMG"


@enum.unique
class ItemStatus(enum.Enum):
    ORDERED = "Ordered"
    FULFILLED = "Fulfilled"
    SHIPPED = "Shipped"
    RETURNED = "Returned"
    REFUNDED = "Refunded"
    BACKORDER = "Backorder"


@enum.unique
class StoreLocation(enum.Enum):
    ARROWHEAD = "Arrowhead"
    CHANDLER = "Chandler"
    AZ_MILLS = "AZ Mills"
    PARK_PLACE = "Park Place"
    SCOTTSDALE = "Scottsdale"
    ONLINE = "Online"


@enum.unique
class OrderType(enum.Enum):
    NEW_ORDER = "New Order"
    FIRST_SUIT = "First Suit"
    RESIZE = "Resize"
    GROOM_RESIZE = "Groom Resize"
    SINGLE_SUIT = "Single Suit"
    SWATCH = "Swatch"
    LOST = "Lost"
    DAMAGED = "Damaged"
    MISSED_ORDER = "Missed Order"
    MISSED_ITEM = "Missed Item"
    ADDRESS_ERROR = "Address Error"
    ADD_ON_ITEM = "Add-On Item"


@enum.unique
class RMAStatus(enum.Enum):
    PENDING = "Pending"
    PENDING_CS_ACTION = "Pending CS Action"
    WAREHOUSE_COMPLETE = "Warehouse Complete"
    WAREHOUSE_CANCELED = "Warehouse Cancelled"
    COMPLETED = "Completed"
    CS_COMPLETE = "CS Complete"


@enum.unique
class RMAType(enum.Enum):
    RESIZE = "Resize"
    DAMAGED = "Damaged"
    CANCELLATION = "Cancellation"
    EXCHANGE = "Exchange"


@enum.unique
class RMAItemType(enum.Enum):
    REFUND = "Refund"
    EXCHANGE = "Exchange"


@enum.unique
class RMAItemReason(enum.Enum):
    DISLIKED = "Disliked"
    TOO_BIG = "Too big"
    TOO_SMALL = "Too small"
    DAMAGED = "Damaged"
    WRONG_ITEM = "Wrong Item"


@enum.unique
class EventType(enum.Enum):
    WEDDING = "wedding"
    PROM = "prom"
    OTHER = "other"


class SerializableMixin:
    def serialize(self):
        columns = inspect(self.__class__).columns.keys()
        return {column: SerializableMixin.normalize(getattr(self, column)) for column in columns}

    @classmethod
    def normalize(cls, value):
        if value is None:
            return None
        elif isinstance(value, list):
            return [SerializableMixin.normalize(v) for v in value]
        elif isinstance(value, uuid.UUID):
            return str(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, enum.Enum):
            return value.name
        elif isinstance(value, dict):
            return {k: SerializableMixin.normalize(v) for k, v in value.items()}

        return value


class Event(Base, SerializableMixin):
    __tablename__ = "events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        unique=True,
        nullable=False,
    )
    name = Column(String, nullable=False)
    event_at = Column(DateTime, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, index=True, default=True, nullable=False)
    type = Column(Enum(EventType), default=EventType.WEDDING, nullable=False)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class Look(Base, SerializableMixin):
    __tablename__ = "looks"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        unique=True,
        nullable=False,
    )
    name = Column(String, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_specs = Column(JSON)
    image_path = Column(String, default=None)
    is_active = Column(Boolean, index=True, default=True, nullable=False)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class Role(Base, SerializableMixin):
    __tablename__ = "roles"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        unique=True,
        nullable=False,
    )
    name = Column(String, index=True, nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    is_active = Column(Boolean, index=True, default=True, nullable=False)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class Attendee(Base, SerializableMixin):
    __tablename__ = "attendees"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        unique=True,
        nullable=False,
    )
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    look_id = Column(UUID(as_uuid=True), ForeignKey("looks.id"))
    style = Column(Boolean, default=False, nullable=False)
    invite = Column(Boolean, default=False, nullable=False)
    pay = Column(Boolean, default=False, nullable=False)
    size = Column(Boolean, default=False, nullable=False)
    ship = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class Address(Base, SerializableMixin):
    __tablename__ = "addresses"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    address_type = Column(String)  # e.g., 'shipping' or 'billing'
    address_line1 = Column(String)
    address_line2 = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    country = Column(String, default="US")
    user = relationship("User", back_populates="addresses")
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class User(Base, SerializableMixin):
    __tablename__ = "users"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    legacy_id = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, nullable=True, unique=True, index=True)
    phone_number = Column(String, default=None, nullable=True)
    shopify_id = Column(String, unique=True)
    orders = relationship("Order", backref="user")
    account_status = Column(Boolean, default=False, nullable=False)
    addresses = relationship("Address", back_populates="user", cascade="all, delete, delete-orphan")
    sms_consent = Column(Boolean, default=False, nullable=True)
    email_consent = Column(Boolean, default=False, nullable=True)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class Order(Base, SerializableMixin):
    __tablename__ = "orders"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    legacy_id = Column(String, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"))
    order_number = Column(String, unique=True)
    shopify_order_id = Column(String, unique=True)
    shopify_order_number = Column(String, unique=True)
    order_origin = Column(Enum(SourceType))
    order_date = Column(DateTime, default=datetime.now(timezone.utc))
    status = Column(String)
    shipped_date = Column(DateTime)
    received_date = Column(DateTime)
    ship_by_date = Column(DateTime)
    shipping_method = Column(String)
    outbound_tracking = Column(String)
    store_location = Column(Enum(StoreLocation))
    order_type = Column(ARRAY(Enum(OrderType)), default=[OrderType.NEW_ORDER])
    shipping_address_line1 = Column(String)
    shipping_address_line2 = Column(String)
    shipping_city = Column(String)
    shipping_state = Column(String)
    shipping_zip_code = Column(String)
    shipping_country = Column(String, default="US")
    meta = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class OrderItem(Base, SerializableMixin):
    __tablename__ = "order_items"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    purchased_price = Column(Numeric)
    quantity = Column(Integer)
    item_status = Column(Enum(ItemStatus), default=ItemStatus.ORDERED)
    order = relationship("Order", backref="order_items")
    product = relationship("Product", backref="order_items")
    shopify_sku = Column(String)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price": self.price,
        }


class Product(Base, SerializableMixin):
    __tablename__ = "products"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    sku = Column(String)
    name = Column(String)
    price = Column(Numeric)
    on_hand = Column(Integer, nullable=False, default=0)
    reserve_inventory = Column(Integer, nullable=False, default=0)
    meta = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class Webhook(Base):
    __tablename__ = "webhooks"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    type = Column(String, nullable=False)
    payload = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=text("now()"), nullable=False)


class RMA(Base):
    __tablename__ = "rmas"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    rma_date = Column(DateTime)  # Date the RMA was created
    updated_at = Column(
        DateTime
    )  # Date the RMA record was last updated # Can this come from and be recorded in History somehow
    rma_number = Column(String)  # Unique identifier for the RMA
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))  # Associated order's primary key
    total_items_expected = Column(Integer)  # Total number of items expected to be returned
    total_items_received = Column(Integer)  # Total number of items actually received
    label_type = Column(String)  # Type of label used for return, e.g., 'Free Label'
    return_tracking = Column(String)  # Tracking number for the return shipment
    internal_return_note = Column(String)  # Internal note for the return
    customer_return_types = Column(String)  # Type of customer return, e.g., 'Refund'
    status = Column(Enum(RMAStatus), default=RMAStatus.PENDING, nullable=False)
    type = Column(ARRAY(Enum(RMAType)), nullable=False)
    reason = Column(String)  # Reason for the return
    is_returned = Column(Boolean)
    is_refunded = Column(Boolean)
    refund_amount = Column(Numeric, nullable=True)
    shiphero_id = Column(String, nullable=True)
    warehouse_notes = Column(String, nullable=True)

    # Relationship to Order model, assuming that Order has a backref to RMADetail
    order = relationship("Order", backref="rmas")


class RMAItem(Base):
    __tablename__ = "rma_items"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    rma_id = Column(UUID(as_uuid=True), ForeignKey("rmas.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    purchased_price = Column(Numeric)
    quantity = Column(Integer)
    quantity_received = Column(Integer)
    type = Column(Enum(RMAItemType), nullable=False)
    reason = Column(Enum(RMAItemReason), nullable=False)
    rma = relationship("RMA", backref="rma_items")


@enum.unique
class DiscountType(enum.Enum):
    GIFT = "gift"
    PARTY_OF_FOUR = "party_of_four"

    def __str__(self):
        return self.value


class Discount(Base, SerializableMixin):
    __tablename__ = "discounts"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    attendee_id = Column(UUID(as_uuid=True), ForeignKey("attendees.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Enum(DiscountType), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    shopify_discount_code = Column(String)
    shopify_discount_code_id = Column(BigInteger)
    shopify_virtual_product_id = Column(BigInteger)
    shopify_virtual_product_variant_id = Column(BigInteger)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class Size(Base, SerializableMixin):
    __tablename__ = "sizes"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    email = Column(String, nullable=True)
    measurement_id = Column(UUID(as_uuid=True), ForeignKey("measurements.id"), nullable=True)
    data = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class Measurement(Base, SerializableMixin):
    __tablename__ = "measurements"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    email = Column(String, nullable=True)
    data = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class Activity(Base):
    __tablename__ = "activities"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)
    data = Column(JSON, default=dict, nullable=False)
    data_md5 = Column(String, nullable=False)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)

    __table_args__ = (Index("ix_user_type", "user_id", "type", "data_md5"),)


@enum.unique
class SuitBuilderItemType(enum.Enum):
    SUIT = "suit"
    SHIRT = "shirt"
    NECK_TIE = "neck_tie"
    BOW_TIE = "bow_tie"
    PREMIUM_POCKET_SQUARE = "premium_pocket_square"
    SHOES = "shoes"
    BELT = "belt"
    SOCKS = "socks"


class SuitBuilderItem(Base):
    __tablename__ = "suit_builder_items"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    type = Column(Enum(SuitBuilderItemType), nullable=False)
    sku = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    index = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    type = Column(String, nullable=False)  # e.g. USER_CREATED, USER_UPDATED, USER_DELETED, ATTENDEE_CREATED, ...
    request = Column(JSONB, default=dict)
    payload = Column(JSONB, default=dict, nullable=False)
    diff = Column(JSONB, default=None, nullable=True)
    created_at = Column(DateTime, default=text("now()"), nullable=False)


class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    audit_log_id = Column(UUID(as_uuid=True), ForeignKey("audit_logs.id"), nullable=False)
    handle = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=text("now()"), nullable=False)


class ShopifyProduct(Base):
    __tablename__ = "shopify_products"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    product_id = Column(BigInteger, nullable=False, unique=True)
    data = Column(JSONB, default=dict, nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=text("now()"), nullable=False)
    updated_at = Column(DateTime, default=text("now()"), nullable=False)
