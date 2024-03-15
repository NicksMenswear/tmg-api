from openapi_server.database.models import Role, User, Event
from openapi_server.database.database_manager import get_database_session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
import uuid
from .hmac_1 import hmac_verification



db = get_database_session()

@hmac_verification()
def create_role(role_data):
    """Create role"""
    try:
        existing_role = db.query(Role).filter(Role.role_name == role_data["role_name"]).first()
        if existing_role:
            return 'Role with the same detail already exists!', 400

        else:
            look_id = uuid.uuid4()
            new_role = Role(
                id=look_id,
                role_name=role_data["role_name"],
                event_id=role_data["event_id"],
                look_id=role_data["look_id"]
            )
            db.add(new_role)
            db.commit()
            db.refresh(new_role)
            return new_role.to_dict()
    except SQLAlchemyError as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()
def get_role(role_id,event_id):
    """List specific role"""
    try:
        existing_event = db.query(Event).filter_by(id=event_id).first()
        if not existing_event:
            return 'Event not found', 204
        role_detail = db.query(Role).filter(Role.id == role_id).first()
        if not role_detail:
            return {'message':'Role not found'}, 204

        return role_detail.to_dict()
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()
def get_event_roles(event_id):
    """List event roles"""
    try:
        event_id = uuid.UUID(event_id)
        existing_event = db.query(Event).filter(Event.id==event_id).first()
        if not existing_event:
            return 'Event not found', 204
        role_details = db.query(Role).filter(Role.event_id == event_id).all()
        if not role_details:
            return 'Role not found', 204

        return [role_detail.to_dict() for role_detail in role_details]
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()
def list_roles():
    """Lists all roles"""
    try:
        role_details = db.query(Role).all()
        if not role_details:
            return {'message':'Role not found'}, 204

        return [role_detail.to_dict() for role_detail in role_details]
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()
def update_role(role_data):
    """Updating Role Details"""
    try:
        role_detail = db.query(Role).filter(Role.role_name == role_data['role_name']).first()
        if not role_detail:
            return {'message':'Role not found'}, 204
        role_detail.role_name = role_data['new_role_name']
        role_detail.look_id = role_data['look_id']
        db.commit()
        return {"message": "Role details updated successfully"}, 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
