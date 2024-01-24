# database_manager.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.realpath(__file__))

env_file_path = os.path.join(current_dir, '../../.env')

load_dotenv(dotenv_path=env_file_path)
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

DATABASE_URL = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

# For Production
# DATABASE_URL = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'


def get_database_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()