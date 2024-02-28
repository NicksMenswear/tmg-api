from openapi_server.database.models import Event, User, Attendee
from openapi_server.database.database_manager import get_database_session
from sqlalchemy.exc import SQLAlchemyError 
from werkzeug.exceptions import HTTPException
import uuid
from .shopify import create_customer, get_customer


db = get_database_session()

def add_attendee(attendee_data):
    """Add Attendee"""
    try:
        user = db.query(User).filter(User.email == attendee_data["email"]).first()
        shopify_user = get_customer(attendee_data['email'])
        if ((not user) and (not shopify_user)):
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
                role = None
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        attendee = db.query(User).filter(User.email == attendee_data["email"]).first()
        existing_attendee = db.query(Event).filter(Event.id == attendee_data["event_id"],Attendee.attendee_id == attendee.id).first()

        if existing_attendee:
            return 'Attendee with the same detail already exists!', 400

        else:
            id = uuid.uuid4()
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
        print(f"An SQLAlchemy error occurred: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")

def list_attendee(email,event_id):
    """List Attendee Detail"""
    try:
        attendee = db.query(User).filter(User.email == email).first()
        if not attendee:
            raise HTTPException(status_code=204, detail="attendee not found")

        attendee_details = db.query(Event).filter(Event.id == event_id, Attendee.attendee_id==attendee.id).first()
        if not attendee_details:
                raise HTTPException(status_code=204, detail="data not found for this event and attendee")
        return attendee_details.to_dict()  # Convert to list of dictionaries

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def update_attendee(attendee_data):
    """Updating Attendee Details"""
    try:
        attendee = db.query(User).filter(User.email == attendee_data['email']).first()
        if not attendee:
            raise HTTPException(status_code=204, detail="attendee not found")

        attendee_detail = db.query(Event).filter(Event.id == attendee_data['event_id'], Attendee.attendee_id==attendee.id).first()
        if not attendee_detail:
                raise HTTPException(status_code=204, detail="data not found for this event and attendee")
        attendee_detail.style = attendee_data['style']
        attendee_detail.invi = attendee_data['invite']
        attendee_detail.pay = attendee_data['pay']
        attendee_detail.size = attendee_data['size']
        attendee_detail.ship = attendee_data['ship']
        db.commit()
        return 'Attendee Updated successfully!', 201
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

def get_attendees_by_eventid(event_id): 
    """List Attendee Detail"""
    try:
        event = db.query(Event).filter(Event.id==event_id).first()
        if not event:
            return 'Event Not Found', 204
        attendees_detail = db.query(Attendee).filter(Attendee.event_id == event_id).all()
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
                'ship' : attendee_detail.ship
            }
            formatted_data.append(data)
        return formatted_data

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")