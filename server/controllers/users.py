from flask import current_app, jsonify

from server.controllers.hmac_1 import hmac_verification
from server.database.database_manager import get_database_session
from server.services.users import UserService, ServiceError

db = get_database_session()


@hmac_verification()
def create_user(user_data):
    user_service = UserService(db, current_app.shopify_service, current_app.email_service)

    existing_user = user_service.get_user_by_email(user_data["email"])
    if existing_user:
        return jsonify({"errors": {"email": ["User with the same email already exists."]}}), 400

    try:
        user = user_service.create_user(
            user_data["first_name"], user_data["last_name"], user_data["email"], user_data["account_status"]
        )
    except ServiceError as e:
        print(e)
        return jsonify({"errors": "Failed to create user."}), 500

    return user.to_dict(), 201


@hmac_verification()
def get_user_by_id(email):
    user_service = UserService(db, current_app.shopify_service, current_app.email_service)

    user = user_service.get_user_by_email(email)

    if not user:
        return {"message": "User not found"}, 404

    return user.to_dict()


@hmac_verification()
def list_users():
    user_service = UserService(db, current_app.shopify_service, current_app.email_service)

    return [user.to_dict() for user in user_service.get_all_users()]


@hmac_verification()
def update_user(user_data):
    user_service = UserService(db, current_app.shopify_service, current_app.email_service)

    user = user_service.get_user_by_email(user_data["email"])

    if not user:
        return jsonify({"errors": ["User not found."]}), 404

    user = user_service.update_user(
        user_data["email"],
        user_data["first_name"],
        user_data["last_name"],
        user_data["account_status"],
        user_data["shopify_id"],
    )

    return user.to_dict()
