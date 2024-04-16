import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    UUID,
    Boolean,
    BigInteger,
    JSON,
    ARRAY,
    VARCHAR,
    Numeric,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from server.database.base_model_ import Model

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    first_name = Column(String, unique=False, index=True, nullable=True)
    last_name = Column(String, unique=False, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    shopify_id = Column(String, unique=True, index=True, nullable=True)
    account_status = Column(Boolean, unique=False, index=True, nullable=True)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "shopify_id": str(self.shopify_id),
            "account_status": self.account_status,
        }
        return result


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    event_name = Column(String, index=True, nullable=False)
    event_date = Column(DateTime, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, index=True, default=True, nullable=False)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            "id": self.id,
            "event_name": self.event_name,
            "event_date": str(self.event_date),
            "user_id": str(self.user_id),
            "is_active": self.is_active,
        }
        return result


class Attendee(Base):
    __tablename__ = "attendees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    attendee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    style = Column(Integer, unique=False, index=True, nullable=False)
    invite = Column(Integer, unique=False, index=True, nullable=False)
    pay = Column(Integer, unique=False, index=True, nullable=False)
    size = Column(Integer, unique=False, index=True, nullable=False)
    ship = Column(Integer, unique=False, index=True, nullable=False)
    is_active = Column(Boolean, index=True, default=True, nullable=False)
    role = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            "id": self.id,
            "attendee_id": self.attendee_id,
            "event_id": str(self.event_id),
            "style": self.style,
            "invite": self.invite,
            "pay": self.pay,
            "size": self.size,
            "ship": self.ship,
            "is_active": self.is_active,
            "role": self.role,
        }
        return result


class ProductItem(Base):
    __tablename__ = "product_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    is_active = Column(Boolean, index=True, default=True, nullable=False)
    name = Column(String, nullable=True)
    sku = Column(String, nullable=True)
    weight_lb = Column(Float, nullable=True)
    height_in = Column(Float, nullable=True)
    width_in = Column(Float, nullable=True)
    length_in = Column(Float, nullable=True)
    value = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    on_hand = Column(Integer, nullable=True)
    allocated = Column(Integer, nullable=True)
    reserve = Column(Integer, nullable=True)
    non_sellable_total = Column(Integer, nullable=True)
    reorder_level = Column(Integer, nullable=True)
    reorder_amount = Column(Integer, nullable=True)
    replenishment_level = Column(Integer, nullable=True)
    available = Column(Integer, nullable=True)
    backorder = Column(Integer, nullable=True)
    barcode = Column(Numeric, nullable=True)
    tags = Column(ARRAY(VARCHAR), nullable=True)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
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
        return result


class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=True)
    order_date = Column(DateTime, default=datetime.utcnow)
    shipped_date = Column(DateTime, nullable=True)
    received_date = Column(DateTime, nullable=True)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "event_id": str(self.event_id),
            "order_date": self.order_date,
            "shipped_date": self.shipped_date,
            "received_date": self.received_date,
        }
        return result


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("product_items.id"), nullable=False)
    quantity = Column(Integer)
    price = Column(Float)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price": self.price,
        }
        return result


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)


class Look(Base):
    __tablename__ = "looks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    look_name = Column(String, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=True)
    product_specs = Column(JSON, nullable=True)
    product_final_image = Column(String, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "look_name": self.look_name,
            "event_id": self.event_id,
            "user_id": self.user_id,
            "product_specs": self.product_specs,
            "product_final_image": self.product_final_image,
        }


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    role_name = Column(String, index=True, nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    look_id = Column(UUID(as_uuid=True), ForeignKey("looks.id"), nullable=False)

    def to_dict(self):
        return {"id": self.id, "role_name": self.role_name, "event_id": self.event_id, "look_id": self.look_id}


class Cart(Base):
    __tablename__ = "carts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=True)
    attendee_id = Column(UUID(as_uuid=True), ForeignKey("attendees.id"), nullable=True)

    cart_products = relationship("CartProduct", back_populates="cart", lazy="dynamic")

    def to_dict(self):
        return {"id": self.id, "user_id": self.user_id, "event_id": self.event_id, "attendee_id": self.attendee_id}


class CartProduct(Base):
    __tablename__ = "cartproducts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id"), nullable=False)
    product_id = Column(BigInteger, index=True, nullable=True)
    variation_id = Column(BigInteger, index=True, nullable=True)
    category = Column(String, index=True, nullable=True)
    quantity = Column(Integer, index=True, nullable=True)
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
