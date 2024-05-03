from sqlalchemy import text

from server.app import init_app, init_db
from server.database.database_manager import db


if __name__ == "__main__":
    print("Resetting db...")
    app = init_app()
    init_db()
    with app.app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()

        try:
            create_extension = text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            conn.execute(create_extension)
            trans.commit()
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

        db.drop_all()
        db.create_all()
