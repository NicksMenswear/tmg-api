import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from openapi_server.database.models import Event, User
from openapi_server.database.database_manager import get_database_session
from sqlalchemy import exists, text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
import uuid


db = get_database_session()

def create_event(event):
    """Create event"""
    try:
        user = db.query(User).filter(User.email == event["email"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        existing_event = db.query(exists().where(Event.event_name == event["event_name"])
                                            .where(Event.event_date == event["event_date"])
                                            .where(Event.attendee == event["attendee"])
                                            .where(Event.user_id == user.id)).scalar()

        if existing_event:
            existing_event = db.query(Event).filter(Event.event_name == event["event_name"],
                                                    Event.event_date == event["event_date"],
                                                    Event.attendee == event["attendee"],
                                                    Event.user_id == user.id).first()

            # existing_event.attendee = event["attendee"]
            existing_event.style = event['style'],
            existing_event.invite = event['invite'],
            existing_event.pay = event['pay'],
            existing_event.size = event['size'],
            existing_event.ship = event['ship']

            db.commit()
            db.refresh(existing_event)
            return existing_event.to_dict()
        else:
            event_id = uuid.uuid4()
            # attendee_json = event["attendee"]
            new_event = Event(
                id=event_id,
                event_name=event["event_name"],
                event_date=event["event_date"],
                user_id=user.id,
                attendee=event["attendee"],
                style = event['style'],
                invite = event['invite'],
                pay = event['pay'],
                size = event['size'],
                ship = event['ship']
            )
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            return new_event.to_dict()
    except SQLAlchemyError as e:
        print(f"An SQLAlchemy error occurred: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


def list_events(username):
    """Lists all events"""
    try:
        user = db.query(User).filter(User.email == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        events = db.query(Event).filter(Event.user_id == user.id).all()

        return [event.to_dict() for event in events]  # Convert to list of dictionaries

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def update_event(event):
    """Updating Event Details. (Currently working on this; will be completed in the next comment)"""
    try:
        event = db.query(Event).filter(Event.id==event['id'],Event.user_id==event['user_id'])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
