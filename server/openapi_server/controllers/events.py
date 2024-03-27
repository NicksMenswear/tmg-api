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
from .hmac_1 import hmac_verification


db = get_database_session()

@hmac_verification()
def create_event(event):
    """Create event"""
    try:
        user = db.query(User).filter(User.email == event["email"]).first()
        if not user:
            return "User not found", 204
        existing_event = db.query(exists().where(Event.event_name == event["event_name"])
                                            .where(Event.event_date == event["event_date"])
                                            .where(Event.user_id == user.id).where(Event.is_active==True)).scalar()

        if existing_event:
            return 'event with the same detail already exists!', 400

        else:
            event_id = uuid.uuid4()
            new_event = Event(
                id=event_id,
                event_name=event["event_name"],
                event_date=event["event_date"],
                user_id=user.id
            )
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            return new_event.to_dict()
    except SQLAlchemyError as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()
def list_events(username):
    """Lists all events"""
    try:
        user = db.query(User).filter(User.email == username).first()
        if not user:
            return "User not found", 204

        events = db.query(Event).filter(Event.user_id == user.id , Event.is_active == True).all()

        return [event.to_dict() for event in events]  # Convert to list of dictionaries

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()
def update_event(event):
    """Updating Event Details."""
    try:
        event_detail = db.query(Event).filter(Event.id==event['id'],Event.user_id==event['user_id']).first()
        if not event_detail:
            return "Event not found", 200
        event_detail.event_date = event['event_date']
        db.commit()
        return "Event details updated successfully", 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500

@hmac_verification()
def soft_delete_event(event):
    """Deleting Event Details."""
    try:
        event_detail = db.query(Event).filter(Event.id==event['event_id']).first()
        if not event_detail:
            return "Event not found", 200
        event_detail.is_active = event['is_active']
        db.commit()
        return "Event details deleted successfully", 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
