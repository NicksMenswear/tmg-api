from server.app import init_app, init_db
from server.database.database_manager import db


if __name__ == "__main__":
    print("Resetting db...")
    app = init_app()
    init_db()
    with app.app.app_context():
        db.drop_all()
        db.create_all()
