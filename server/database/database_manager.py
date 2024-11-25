import os

db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD", "postgres")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", 5432)
db_name = os.getenv("DB_NAME", "tmg")
db_pool_size = int(os.getenv("DB_POOL_SIZE", 1))


DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


engine_options = dict(
    pool_timeout=3,
    pool_size=db_pool_size,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo_pool=True,
)

if os.getenv("USE_FLASK") == "false":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)

    class DBManager:
        def __init__(self):
            self.session = Session()

    db = DBManager()
else:
    from flask_sqlalchemy import SQLAlchemy

    db = SQLAlchemy(engine_options=engine_options)
