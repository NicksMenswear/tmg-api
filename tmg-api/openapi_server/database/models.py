from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Define the many-to-many relationship table between Users and Events
user_events_table = Table('user_events', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('event_id', Integer, ForeignKey('events.id'))
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    date = Column(DateTime)

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
    price = Column(Float)  # Optional, if you want to record price per item at order time
    order = relationship("Order", back_populates="items")
    catalog_item = relationship("CatalogItem")

# You might also want to include an AuditLog model if you have audit logging
class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True)
    # ... other fields for your audit log ...

# Remember to import and call Base.metadata.create_all(engine) in your application startup code to create these tables.
