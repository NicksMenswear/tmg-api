#!/usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from openapi_server.database.models import Base, User, Event, CatalogItem, Order, OrderItem, AuditLog  # Import your models

# Replace 'DATABASE_URL' with your actual database URL
DATABASE_URL = 'postgresql://myuser:mypassword@postgres:5432/mydatabase'
engine = create_engine(DATABASE_URL)

# Create tables
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Close the session when done
session.close()
