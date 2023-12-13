from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Table, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from openapi_server.models.base_model_ import Model
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    first_name = Column(String, unique=False, index=True, nullable=False)
    last_name = Column(String, unique=False, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    shopify_id = Column(String, unique=True, index=True, nullable=False)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'shopify_id':self.shopify_id
        }
        return result

class Event(Base, Model):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    event_name = Column(String, index=True, nullable=False)
    event_date = Column(DateTime, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    attendees = Column(String)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        result = {
            'id': str(self.id),
            'event_name': self.event_name,
            'event_date': str(self.event_date),
            'user_id': str(self.user_id),
            'attendees': self.attendees
        }
        return result

class CatalogItem(Base):
    __tablename__ = 'catalog_items'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_id = Column(Integer, ForeignKey('events.id'))
    order_date = Column(DateTime, default=datetime.utcnow)
    shipped_date = Column(DateTime, nullable=True)
    received_date = Column(DateTime, nullable=True)
    user = relationship("User")
    event = relationship("Event")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    catalog_item_id = Column(Integer, ForeignKey('catalog_items.id'))
    quantity = Column(Integer)
    price = Column(Float)
    order = relationship("Order", back_populates="items")
    catalog_item = relationship("CatalogItem")

class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True)

