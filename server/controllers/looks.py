import uuid

from flask import jsonify
from flask import current_app as app

from server.controllers.hmac_1 import hmac_verification
from server.database.database_manager import get_database_session, session_factory
from server.database.models import Look, User, Role, Attendee, Event
from server.services import NotFoundError, ServiceError, DuplicateError
from server.services.look import LookService
from server.services.user import UserService

db = get_database_session()


@hmac_verification()
def create_look(look_data):
    session = session_factory()

    look_service = LookService(session)
    user_service = UserService(session)

    user = user_service.get_user_by_email(look_data["email"])

    if not user:
        return jsonify({"errors": "User not found"}), 404

    try:
        del look_data["email"]
        enriched_look_data = {**look_data, "user_id": user.id}

        look = look_service.create_look(**enriched_look_data)
    except DuplicateError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 409
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": "Failed to create look"}), 500

    return look.to_dict(), 201


@hmac_verification()
def get_look(look_id, user_id):
    look_service = LookService(session_factory())

    look = look_service.get_look_by_id_and_user(look_id, user_id)

    if not look:
        return jsonify({"errors": NotFoundError.MESSAGE}), 404

    return look.to_dict(), 200


@hmac_verification()
def get_user_looks(user_id):
    look_service = LookService(session_factory())

    looks = look_service.get_looks_for_user(user_id)

    return [look.to_dict() for look in looks]


@hmac_verification()
def list_looks():
    look_service = LookService(session_factory())

    return [look.to_dict() for look in look_service.get_all_looks()], 200


@hmac_verification()
def update_look(look_data):
    """Updating Look Details"""
    try:
        existing_user = db.query(User).filter_by(email=look_data["email"]).first()
        if not existing_user:
            return "User not found", 204
        look_detail = (
            db.query(Look).filter(Look.id == look_data["look_id"], Look.event_id == look_data["event_id"]).first()
        )
        if not look_detail:
            return "Look not found", 204

        look_id = uuid.uuid4()
        new_look = Look(
            id=look_id,
            look_name=look_data["look_name"],
            event_id=look_data["event_id"],
            user_id=look_data["user_id"],
            product_specs=look_data["product_specs"],
            product_final_image=look_data["product_final_image"],
        )
        db.add(new_look)
        db.commit()
        db.refresh(new_look)

        role_detail = (
            db.query(Role).filter(Role.look_id == look_data["look_id"], Role.event_id == look_data["event_id"]).first()
        )
        if not role_detail:
            return "Role not found", 204

        role_id = uuid.uuid4()
        new_role = Role(id=role_id, role_name=role_detail.role_name, event_id=role_detail.event_id, look_id=look_id)
        db.add(new_role)
        db.commit()
        db.refresh(new_role)

        attendee_detail = (
            db.query(Attendee)
            .filter(Attendee.id == look_data["attendee_id"], Attendee.event_id == look_data["event_id"])
            .first()
        )

        if not attendee_detail:
            return "attendee not found", 204
        else:
            attendee_detail.role = role_id
            db.commit()
            return "Look details updated successfully", 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
