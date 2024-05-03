#!/usr/bin/env python

import os

from sqlalchemy import create_engine, text

from server.database.models import Base

DATABASE_URL = os.getenv("DB_URI")
engine = create_engine(DATABASE_URL, echo=True)

# Init extensions
create_extension = text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
    connection.execute(create_extension)

# Init schema
Base.metadata.create_all(engine, checkfirst=True)
