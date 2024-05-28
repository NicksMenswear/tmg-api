import enum
import uuid
from datetime import datetime

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
    VARCHAR,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

try:
    from flask_sqlalchemy import SQLAlchemy
    from server.database.database_manager import db

    Base = db.Model
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()


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


class Event(Base):
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
    event_at = Column(DateTime)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, index=True, default=True, nullable=False)


class Look(Base):
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


class Role(Base):
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


class Attendee(Base):
    __tablename__ = "attendees"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        unique=True,
        nullable=False,
    )
    attendee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    role = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    look_id = Column(UUID(as_uuid=True), ForeignKey("looks.id"))
    style = Column(Integer, nullable=False)
    invite = Column(Integer, nullable=False)
    pay = Column(Integer, nullable=False)
    size = Column(Integer, nullable=False)
    ship = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


# class CurrentSize(Base):
#     __tablename__ = 'current_sizes'
# id = Column(UUID(as_uuid=True),
#     primary_key=True,
#     default=uuid.uuid4,
#     server_default=text("uuid_generate_v4()"),
#     nullable=False)
#     age = Column(String)
#     height = Column(String)
#     weight = Column(Integer)
#     inch = Column(String)
#     chest_structure = Column(String)
#     stomach_structure = Column(String)
#     jean_waist_size = Column(Integer)
#     waist = Column(Integer)
#     suit_size = Column(String)  # Assuming "-" in the image represents a nullable field
#     dress_shirt_size = Column(Integer)
#     chest_size = Column(Integer)
#     neck_size = Column(Numeric)
#     sleeve_size = Column(Integer)
#     t_shirt_size = Column(String)
#     shoes_size = Column(Integer)
#     seat = Column(Integer)
#     jacket_waist = Column(Integer)
#     user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))  # Link to the User model

#     # Relationship back to the User model
#     user = relationship('User', back_populates='current_size')

# class HistoricalSize(Base):
#     __tablename__ = 'historical_sizes'
# id = Column(UUID(as_uuid=True),
#     primary_key=True,
#     default=uuid.uuid4,
#     server_default=text("uuid_generate_v4()"),
#     nullable=False)
#     user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
#     measurement_date = Column(DateTime, default=datetime.utcnow)
#     suit_size_sent = Column(String)
#     event_completed = Column(DateTime)
#     age = Column(String)
#     height = Column(String)
#     weight = Column(Integer)
#     inch = Column(String)
#     chest_structure = Column(String)
#     stomach_structure = Column(String)
#     jean_waist_size = Column(Integer)
#     waist = Column(Integer)
#     suit_size = Column(String)  # Assuming "-" in the image represents a nullable field
#     dress_shirt_size = Column(Integer)
#     chest_size = Column(Integer)
#     neck_size = Column(Numeric)
#     sleeve_size = Column(Integer)
#     t_shirt_size = Column(String)
#     shoes_size = Column(Integer)
#     seat = Column(Integer)
#     jacket_waist = Column(Integer)
#     user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))  # Link to the User model

#     # Relationship back to the User model
#     # user = relationship('User', back_populates='current_size')
#     user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))

#     user = relationship('User', back_populates='historical_sizes')


# # Define the Address model
class Address(Base):
    __tablename__ = "addresses"
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    # user_id = Column(Integer, ForeignKey('users.id'))
    address_type = Column(String)  # e.g., 'shipping' or 'billing'
    address_line1 = Column(String)  # Primary address line (e.g., street address, P.O. box)
    address_line2 = Column(String)  # Secondary address line (e.g., apartment, suite number)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    country = Column(String, default="US")  # Default set to 'US', change as needed
    # Relationship back to the User model
    user = relationship("User", back_populates="addresses")


class User(Base):
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
    phone_number = Column(String)
    shopify_id = Column(String, unique=True)
    orders = relationship("Order", backref="user")
    account_status = Column(Boolean)
    addresses = relationship("Address", back_populates="user", cascade="all, delete, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )

    legacy_id = Column(String, unique=True)  # for consistency checking with legacy db
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"))
    order_number = Column(String, unique=True)
    order_origin = Column(Enum(SourceType))
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String)
    shipped_date = Column(DateTime)
    received_date = Column(DateTime)
    ship_by_date = Column(DateTime)
    shipping_method = Column(String)
    outbound_tracking = Column(String)
    store_location = Column(Enum(StoreLocation))
    order_type = Column(ARRAY(Enum(OrderType)), default=[OrderType.NEW_ORDER])

    # Shipping address snapshot
    shipping_address_line1 = Column(String)  # Snapshot of address line 1
    shipping_address_line2 = Column(String)  # Snapshot of address line 2
    shipping_city = Column(String)
    shipping_state = Column(String)
    shipping_zip_code = Column(String)
    shipping_country = Column(String, default="US")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "event_id": str(self.event_id),
            "order_date": self.order_date,
            "shipped_date": self.shipped_date,
            "received_date": self.received_date,
        }


class OrderItem(Base):
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
    price = Column(Float)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price": self.price,
        }


class ProductItem(Base):
    __tablename__ = "product_items"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    is_active = Column(Boolean, index=True, default=True, nullable=False)
    name = Column(String)
    sku = Column(String)
    weight_lb = Column(Float)
    height_in = Column(Float)
    width_in = Column(Float)
    length_in = Column(Float)
    value = Column(Float)
    price = Column(Float)
    on_hand = Column(Integer)
    allocated = Column(Integer)
    reserve = Column(Integer)
    non_sellable_total = Column(Integer)
    reorder_level = Column(Integer)
    reorder_amount = Column(Integer)
    replenishment_level = Column(Integer)
    available = Column(Integer)
    backorder = Column(Integer)
    barcode = Column(Numeric)
    tags = Column(ARRAY(VARCHAR))

    def to_dict(self):
        return {
            "id": self.id,
            "is_active": self.is_active,
            "name": self.name,
            "sku": self.sku,
            "weight_lb": self.weight_lb,
            "height_in": self.height_in,
            "width_in": self.width_in,
            "length_in": self.length_in,
            "value": self.value,
            "price": self.price,
            "on_hand": self.on_hand,
            "allocated": self.allocated,
            "reserve": self.reserve,
            "non_sellable_total": self.non_sellable_total,
            "reorder_level": self.reorder_level,
            "reorder_amount": self.reorder_amount,
            "replenishment_level": self.replenishment_level,
            "available": self.available,
            "backorder": self.backorder,
            "barcode": self.barcode,
            "tags": self.tags,
        }


class Product(Base):
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


class Cart(Base):
    __tablename__ = "carts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"))
    attendee_id = Column(UUID(as_uuid=True), ForeignKey("attendees.id"))
    cart_products = relationship("CartProduct", back_populates="cart", lazy="dynamic")

    def to_dict(self):
        return {"id": self.id, "user_id": self.user_id, "event_id": self.event_id, "attendee_id": self.attendee_id}


class CartProduct(Base):
    __tablename__ = "cartproducts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"), nullable=False)
    product_id = Column(BigInteger)
    variation_id = Column(BigInteger)
    category = Column(String)
    quantity = Column(Integer)
    cart = relationship("Cart", back_populates="cart_products")

    def to_dict(self):
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "variation_id": self.variation_id,
            "category": self.category,
            "quantity": self.quantity,
        }


@enum.unique
class DiscountType(enum.Enum):
    GROOM_GIFT = "groom_gift"
    GROOM_FULL_PAY = "groom_full_pay"
    PARTY_OF_FOUR = "party_of_four"

    def __str__(self):
        return self.value


class Discount(Base):
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
    amount = Column(Integer, nullable=False)
    type = Column(Enum(DiscountType), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    shopify_discount_code = Column(String)
    shopify_discount_code_id = Column(BigInteger)
    shopify_virtual_product_id = Column(BigInteger)
    shopify_virtual_product_variant_id = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
