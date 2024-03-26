from database.models import Look, User, Role, Attendee, Event
from database.database_manager import get_database_session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
import numpy as np
from .hmac_1 import hmac_verification
import uuid


db = get_database_session()


@hmac_verification()    
def create_look(look_data):
    """Create look"""
    try:
        existing_user = db.query(User).filter_by(email=look_data['email']).first()
        if not existing_user:
            return 'User not found', 204
        if look_data["look_name"]=="":
            return 'Look name cannot be empty', 400

        existing_look = db.query(Look).filter(Look.look_name == look_data["look_name"], Look.user_id==existing_user.id).first()
        if existing_look and existing_user:
            return 'Look with the same detail already exists!', 400
        if "event_id" not in look_data:
            look_data['event_id'] = None

        look_id = uuid.uuid4()
        new_look = Look(
            id=look_id,
            look_name=look_data["look_name"],
            event_id=look_data["event_id"],
            user_id=existing_user.id,
            product_specs=look_data["product_specs"],
            product_final_image = look_data["product_final_image"]
        )
        db.add(new_look)
        db.commit()
        db.refresh(new_look)
        return new_look.to_dict()
        # return 'Look created successfully!', 201
    except SQLAlchemyError as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()    
def get_look(look_id,user_id):
    """List specific look"""
    try:
        db = get_database_session()
        existing_user = db.query(User).filter_by(id=user_id).first()
        if not existing_user:
            return 'User not found', 204
        look_detail = db.query(Look).filter(Look.id == look_id, Look.user_id == user_id).first()

        if not look_detail:
            return 'Look not found', 204

        return look_detail.to_dict()
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()    
def get_look_userid_eventid(user_id,event_id=None):
    """List looks based on user_id and event_id"""
    try:
        db = get_database_session()
        existing_user = db.query(User).filter_by(id=user_id).first()
        if not existing_user:
            return 'User not found', 204
        if event_id==None:
            look_details = db.query(Look).filter(Look.user_id == user_id).all()
            if not look_details:
                return 'Look not found', 204
            formatted_data = []
            for look in look_details:
                event = db.query(Event).filter(Event.id == look.event_id , Event.is_active == True).first()
                if event:
                    data = {
                        'event_name': event.event_name,
                        'look_data': {
                        'id': look.id,
                        'look_name': look.look_name,
                        'user_id': look.user_id,
                        'product_specs': look.product_specs,
                        'product_final_image': look.product_final_image,
                        'event_id': look.event_id
                        }
                    }
                    formatted_data.append(data)
                else:
                    data = {
                        'event_name': np.nan,
                        'look_data': {
                        'id': look.id,
                        'look_name': look.look_name,
                        'user_id': look.user_id,
                        'product_specs': look.product_specs,
                        'product_final_image': look.product_final_image,
                        'event_id': np.nan
                        }
                    }
                    formatted_data.append(data)
            return formatted_data
        else:
            look_details = db.query(Look).filter(Look.user_id == user_id, Look.event_id == event_id).all()
            if not look_details:
                return 'Look not found', 204
            event = db.query(Event).filter(Event.id == event_id , Event.is_active == True).first()
            formatted_data = []
            if event:
                for look in look_details:               
                    data = {
                        'event_name': event.event_name,
                        'look_data': {
                        'id': look.id,
                        'look_name': look.look_name,
                        'user_id': look.user_id,
                        'product_specs': look.product_specs,
                        'product_final_image': look.product_final_image,
                        'event_id': look.event_id
                        }
                    }
                    formatted_data.append(data)
                return formatted_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    
@hmac_verification()    
def get_user_looks(user_id):
    """Specific user looks"""
    try:
        db = get_database_session()
        user_id = uuid.UUID(user_id)
        existing_user = db.query(User).filter_by(id=user_id).first()
        if not existing_user:
            return 'User not found', 204
        look_details = db.query(Look).filter(Look.user_id == user_id).all()
        print()
        if not look_details:
            return 'Look not found', 204

        return [look_detail.to_dict() for look_detail in look_details]
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    
@hmac_verification()    
def list_looks():
    """Lists all looks"""
    try:
        look_details = db.query(Look).all()
        if not look_details:
            return 'Look not found', 204

        return [look_detail.to_dict() for look_detail in look_details]
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()    
def update_look(look_data):
    """Updating Look Details"""
    try:
        existing_user = db.query(User).filter_by(email=look_data['email']).first()
        if not existing_user:
            return 'User not found', 204
        look_detail = db.query(Look).filter(Look.id == look_data['look_id'], Look.event_id == look_data['event_id']).first()
        if not look_detail:
            return 'Look not found', 204

        look_id = uuid.uuid4()
        new_look = Look(
            id=look_id,
            look_name=look_data["look_name"],
            event_id=look_data["event_id"],
            user_id=look_data["user_id"],
            product_specs=look_data["product_specs"],
            product_final_image = look_data["product_final_image"]
        )
        db.add(new_look)
        db.commit()
        db.refresh(new_look)
    
        role_detail = db.query(Role).filter(Role.look_id==look_data['look_id'], Role.event_id == look_data['event_id']).first()
        if not role_detail:
            return 'Role not found', 204
        
        role_id = uuid.uuid4()
        new_role = Role(
            id=role_id,
            role_name=role_detail.role_name,
            event_id=role_detail.event_id,
            look_id=look_id
        )
        db.add(new_role)
        db.commit()
        db.refresh(new_role)

        attendee_detail = db.query(Attendee).filter(Attendee.id==look_data['attendee_id'], Attendee.event_id == look_data['event_id']).first()

        if not attendee_detail:
            return 'attendee not found', 204
        else:
            attendee_detail.role = role_id
            db.commit()
            return "Look details updated successfully", 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
