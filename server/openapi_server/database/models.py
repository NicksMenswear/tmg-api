from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, UUID, Boolean
from sqlalchemy.ext.declarative import declarative_base
from openapi_server.models.base_model_ import Model
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    first_name = Column(String, unique=False, index=True, nullable=True)
    last_name = Column(String, unique=False, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    shopify_id = Column(String, unique=True, index=True, nullable=True)
    account_status = Column(Boolean, unique=False, index=True, nullable=True)
    role = Column(String, unique=False, index=True, nullable=True)


    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'shopify_id':str(self.shopify_id),
            'account_status' : self.account_status,
            'role' : self.role
        }
        return result

class Event(Base, Model):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    event_name = Column(String, index=True, nullable=False)
    event_date = Column(DateTime, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            'id': self.id,
            'event_name': self.event_name,
            'event_date': str(self.event_date),
            'user_id': str(self.user_id)
        }
        return result

class Attendee(Base, Model):
    __tablename__ = "attendees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    attendee_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'), nullable=False)
    style = Column(Integer, unique=False, index=True, nullable=False)
    invite = Column(Integer, unique=False, index=True, nullable=False)
    pay = Column(Integer, unique=False, index=True, nullable=False)
    size = Column(Integer, unique=False, index=True, nullable=False)
    ship = Column(Integer, unique=False, index=True, nullable=False)


    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            'id': self.id,
            'event_id': str(self.event_id),
            'style': self.style,
            'invite': self.invite,
            'pay': self.pay,
            'size': self.size,
            'ship': self.ship
        }
        return result
class ProductItem(Base):
    __tablename__ = 'product_items'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String,unique=True, nullable=False)
    price = Column(Float,nullable=False)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            'id': self.id,
            'name': self.name,
            'price': self.price
        }
        return result

class Order(Base):
    __tablename__ = 'orders'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'), nullable=True)
    order_date = Column(DateTime, default=datetime.utcnow)
    shipped_date = Column(DateTime, nullable=True)
    received_date = Column(DateTime, nullable=True)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'event_id': str(self.event_id),
            'order_date': self.order_date,
            'shipped_date': self.shipped_date,
            'received_date': self.received_date,
        }
        return result

class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('product_items.id'), nullable=False)
    quantity = Column(Integer)
    price = Column(Float)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price
        }
        return result

class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True)

class Look(Base, Model):
    __tablename__ = "looks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    look_name = Column(String, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    product_specs = Column(String, index=True, nullable=True)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            'id': self.id,
            'look_name': self.look_name,
            'user_id': self.user_id,
            'product_specs': self.product_specs
        }
        return result
    
class Role(Base, Model):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    role_name = Column(String, index=True, nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'), nullable=False)
    look_id = Column(UUID(as_uuid=True), ForeignKey('looks.id'), nullable=False)


    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            'id': self.id,
            'role_name': self.role_name,
            'event_id': self.event_id,
            'look_id': self.look_id
        }
        return result
