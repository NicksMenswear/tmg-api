from openapi_server.database.models import Look, User, Role
from openapi_server.database.database_manager import get_database_session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
import uuid


db = get_database_session()

def create_look(look_data):
    """Create look"""
    try:
        existing_user = db.query(User).filter_by(email=look_data['email']).first()
        if not existing_user:
            return 'User not found', 204
        existing_look = db.query(Look).filter(Look.look_name == look_data["look_name"], Look.user_id==existing_user.id).first()
        if existing_look and existing_user:
            return 'Look with the same detail already exists!', 400

        else:
            look_id = uuid.uuid4()
            new_look = Look(
                id=look_id,
                look_name=look_data["look_name"],
                user_id=existing_user.id,
                product_specs=look_data["product_specs"]
            )
            db.add(new_look)
            db.commit()
            db.refresh(new_look)
            return new_look.to_dict()
    except SQLAlchemyError as e:
        print(f"An SQLAlchemy error occurred: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


def get_look(look_id,user_id):
    """List specific look"""
    try:
        existing_user = db.query(User).filter_by(id=user_id).first()
        if not existing_user:
            return 'User not found', 204
        look_detail = db.query(Look).filter(Look.id == look_id, Look.user_id == user_id).first()
        if not look_detail:
            raise HTTPException(status_code=204, detail="Look not found")

        return look_detail.to_dict()
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
def get_user_looks(user_id):
    """Specific user looks"""
    try:
        user_id = uuid.UUID(user_id)
        existing_user = db.query(User).filter_by(id=user_id).first()
        if not existing_user:
            return 'User not found', 204
        look_details = db.query(Look).filter(Look.user_id == user_id).all()
        if not look_details:
            raise HTTPException(status_code=204, detail="Look not found")

        return [look_detail.to_dict() for look_detail in look_details]
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
def list_looks():
    """Lists all looks"""
    try:
        look_details = db.query(Look).all()
        if not look_details:
            raise HTTPException(status_code=204, detail="Look not found")

        return [look_detail.to_dict() for look_detail in look_details]
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def update_look(look_data):
    """Updating Look Details"""
    try:
        existing_user = db.query(User).filter_by(email=look_data['email']).first()
        if not existing_user:
            return 'User not found', 204
        look_detail = db.query(Look).filter(Look.look_name == look_data['look_name']).first()
        role_detail = db.query(Role).filter(Role.look_id==look_detail.id) 
        if not look_detail:
            raise HTTPException(status_code=404, detail="Look not found")
        if not role_detail:
            raise HTTPException(status_code=404, detail="Role not found")

        if role_detail:
            if look_data['flag']==False:
                return 'Record already Exists', 409
            else:
                look_detail.product_specs = look_data['product_specs']
                db.commit()
                return {"message": "Look details updated successfully"}, 200
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
