from openapi_server.database.models import Event, User, Attendee
from openapi_server.database.database_manager import get_database_session
from sqlalchemy.exc import SQLAlchemyError 
from werkzeug.exceptions import HTTPException
import uuid
from .shopify import create_customer, get_customer
from .hmac_1 import hmac_verification



db = get_database_session()

@hmac_verification()
def add_attendee(attendee_data):
    """Add Attendee"""
    try:
        user = db.query(User).filter(User.email == attendee_data["email"]).first()
        print("================= User: ", user)
        if user:
            return 'Attendee with the same detail already exists!', 400
        shopify_user = get_customer(attendee_data['email'])
        print(" ===================== shopify: ",shopify_user)
        if ((not user) and (not shopify_user)):
            print("------------ Inside")
            shopify_id = create_customer({
                'first_name' : attendee_data['first_name'],
                'last_name' : attendee_data['last_name'],
                'email' : attendee_data['email'],
            })
            user_id = uuid.uuid4()
            user = User(
                id=user_id,
                first_name=attendee_data['first_name'],
                last_name=attendee_data['last_name'],
                email=attendee_data['email'],
                shopify_id=shopify_id,
                account_status = True,
                role=attendee_data['role']
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        attendee = db.query(User).filter(User.email == attendee_data["email"]).first()
        print(" ============== attendee: ", attendee)
        existing_attendee = db.query(Attendee).filter(Attendee.event_id == attendee_data["event_id"],Attendee.attendee_id == attendee.id, Attendee.is_active == True).first()

        if existing_attendee:
            return 'Attendee with the same detail already exists!', 400
        

        else:
            id = uuid.uuid4()
            user.first_name = attendee_data['first_name']
            user.last_name = attendee_data['last_name']
            user.role = attendee_data['role']
            user.account_status = True

            db.commit()
            db.refresh(user)

            new_attendee = Attendee(
                id=id,
                attendee_id = attendee.id,
                event_id=attendee_data["event_id"],
                style = attendee_data['style'],
                invite = attendee_data['invite'],
                pay = attendee_data['pay'],
                size = attendee_data['size'],
                ship = attendee_data['ship']
            )
            db.add(new_attendee)
            db.commit()
            db.refresh(new_attendee)
            return 'Attendee created successfully!', 201
    except SQLAlchemyError as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    
@hmac_verification()
def list_attendee(email,event_id):
    """List Attendee Detail"""
    try:
        attendee = db.query(User).filter(User.email == email).first()
        if not attendee:
            return {'message':'attendee not found'}, 204

        attendee_details = db.query(Event).filter(Event.id == event_id, Attendee.attendee_id==attendee.id , Event.is_active==True , Attendee.is_active == True).first()
        if not attendee_details:
            return {'message':'data not found for this event and attendee'}, 204
            
        return attendee_details.to_dict()  # Convert to list of dictionaries

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    
@hmac_verification()
def update_attendee(attendee_data):
    """Updating Attendee Details"""
    try:
        attendee = db.query(User).filter(User.email == attendee_data['email']).first()
        if not attendee:
            return {'message':'attendee not found'}, 204

        attendee_detail = db.query(Event).filter(Event.id == attendee_data['event_id'], Attendee.attendee_id==attendee.id).first()
        if not attendee_detail:
            return {'message':'data not found for this event and attendee'}, 204

        attendee_detail.style = attendee_data['style']
        attendee_detail.invi = attendee_data['invite']
        attendee_detail.pay = attendee_data['pay']
        attendee_detail.size = attendee_data['size']
        attendee_detail.ship = attendee_data['ship']
        db.commit()
        return 'Attendee Updated successfully!', 201
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    
@hmac_verification()
def get_attendees_by_eventid(event_id): 
    """List Attendee Detail"""
    try:
        event = db.query(Event).filter(Event.id==event_id).first()
        if not event:
            return 'Event Not Found', 204
        attendees_detail = db.query(Attendee).filter(Attendee.event_id == event_id ,Attendee.is_active==True , Event.is_active == True).all()
        if not attendees_detail:
            return 'No Attendee For This Event Found', 204
        formatted_data = []
        for attendee_detail in attendees_detail:
            attendee = db.query(User).filter(User.id==attendee_detail.attendee_id).first()
            data = {
                'id': attendee_detail.id,
                'first_name': attendee.first_name,
                'last_name': attendee.last_name,
                'email': attendee.email,
                'account_status': attendee.account_status,
                'event_id': attendee_detail.event_id,
                'style' : attendee_detail.style,
                'invite' : attendee_detail.invite,
                'pay' : attendee_detail.pay,
                'size' : attendee_detail.size,
                'ship' : attendee_detail.ship,
                'is_Active' : attendee_detail.is_active
            }
            formatted_data.append(data)
        return formatted_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    
@hmac_verification()    
def soft_delete_attendee(attendee_data):
    """Deleteing Attendee Details"""
    try:
        attendee = db.query(User).filter(User.email == attendee_data['email']).first()
        if not attendee:
            return "attendee not found" , 200

        attendee_detail = db.query(Attendee).filter(Attendee.event_id == attendee_data['event_id'], Attendee.id==attendee_data['attendee_id']).first()

        if not attendee_detail:
            return 'data not found for this event and attendee', 200
        
        attendee_detail.is_active = attendee_data['is_active']
       
        db.commit()
        return 'Attendee Deleted successfully!', 200
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
