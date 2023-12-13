# database_manager.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Define the database URL
DATABASE_URL = 'postgresql://postgres:123456@localhost:5432/TMG'

# Create a function to establish a database session
def get_database_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()