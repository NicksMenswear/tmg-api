import uuid
from urllib.parse import unquote

from flask import current_app

from server.controllers.hmac_1 import hmac_verification
from server.database.database_manager import get_database_session
from server.database.models import User

db = get_database_session()


@hmac_verification()
def create_user(user_data):
    try:
        existing_user = db.query(User).filter_by(email=user_data["email"]).first()
        if existing_user:
            return "User with the same email already exists in TMG Database!", 400

        try:
            shopify_id = current_app.shopify_service.create_customer(
                user_data["first_name"], user_data["last_name"], user_data["email"]
            )["id"]
        except Exception as e:
            print(e)
            return "User not created in shopify", 400

        user_id = uuid.uuid4()

        user = User(
            id=user_id,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            shopify_id=shopify_id,
            account_status=user_data["account_status"],
        )

        db.add(user)

        current_app.email_service.send_activation_url(user_data["email"], shopify_id)

        db.commit()
        db.refresh(user)

        return user.to_dict(), 201
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def get_user_by_id(email):
    try:
        email = unquote(email)
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {"message": f"User with email '{email}' does not exist"}, 404
        formatted_user = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "shopify_id": user.shopify_id,
            "account_status": user.account_status,
        }
        return formatted_user
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def list_users():
    try:
        formatted_users = []
        users = db.query(User).all()
        for user in users:
            formatted_user = {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "shopify_id": user.shopify_id,
                "account_status": user.account_status,
            }
            formatted_users.append(formatted_user)
        return formatted_users
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def update_user(user_data):
    try:
        user = db.query(User).filter(User.email == user_data["email"]).first()

        if not user:
            return {"message": "User not found"}, 404

        user.first_name = user_data["first_name"]
        user.last_name = user_data["last_name"]
        user.shopify_id = user_data["shopify_id"]
        user.account_status = user_data["account_status"]

        db.commit()
        db.refresh(user)

        return user.to_dict(), 200
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
