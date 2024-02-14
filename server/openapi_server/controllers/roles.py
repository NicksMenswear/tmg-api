from openapi_server.database.models import Role, User
from openapi_server.database.database_manager import get_database_session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
import uuid


db = get_database_session()

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
        print(f"An SQLAlchemy error occurred: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

def get_role(role_data):
    """List specific role"""
    try:
        role_detail = db.query(Role).filter(Role.role_name == role_data).first()
        if not role_detail:
            raise HTTPException(status_code=404, detail="Look not found")

        return role_detail.to_dict()
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
def list_roles():
    """Lists all roles"""
    try:
        role_details = db.query(Role).all()
        if not role_details:
            raise HTTPException(status_code=404, detail="Role not found")

        return [role_detail.to_dict() for role_detail in role_details]
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def update_role(role_data):
    """Updating Role Details"""
    try:
        role_detail = db.query(Role).filter(Role.role_name == role_data['role_name']).first()
        if not role_detail:
            raise HTTPException(status_code=404, detail="Role not found")
        role_detail.role_name = role_data['new_role_name']
        role_detail.look_id = role_data['look_id']
        db.commit()
        return {"message": "Role details updated successfully"}, 200
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
