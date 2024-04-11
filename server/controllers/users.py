from flask import jsonify

from server.controllers.hmac_1 import hmac_verification
from server.database.database_manager import session_factory
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.users import UserService


@hmac_verification()
def create_user(user_data):
    user_service = UserService(session_factory())

    try:
        user = user_service.create_user(**user_data)
    except DuplicateError as e:
        print(str(e))
        return jsonify({"errors": DuplicateError.MESSAGE}), 409
    except ServiceError as e:
        print(str(e))
        return jsonify({"errors": "Failed to create user"}), 500

    return user.to_dict(), 201


@hmac_verification()
def get_user_by_id(email):
    user_service = UserService(session_factory())

    user = user_service.get_user_by_email(email)

    if not user:
        return jsonify({"errors": NotFoundError.MESSAGE}), 404

    return user.to_dict(), 200


@hmac_verification()
def list_users():
    user_service = UserService(session_factory())

    return [user.to_dict() for user in user_service.get_all_users()], 200


@hmac_verification()
def update_user(user_data):
    user_service = UserService(session_factory())

    try:
        user = user_service.update_user(**user_data)
    except NotFoundError as e:
        print(e)
        return jsonify({"errors": NotFoundError.MESSAGE}), 404
    except ServiceError as e:
        print(e)
        return jsonify({"errors": "Failed to update user."}), 500

    return user.to_dict(), 200
