import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from database.models import Event, User
from database.database_manager import get_database_session
from sqlalchemy import exists, text
from sqlalchemy.exc import SQLAlchemyError
from flask import abort
import uuid


db = get_database_session()

def create_event(event):
    """Create event"""
    try:
        user = db.query(User).filter(User.email == event["email"]).first()
        if not user:
            raise abort(404, description="User not found")

        existing_event = db.query(exists().where(Event.event_name == event["event_name"])
                                            .where(Event.event_date == event["event_date"])
                                            .where(Event.user_id == user.id)).scalar()

        if existing_event:
            return 'event with the same detail already exists!', 400

        else:
            event_id = uuid.uuid4()
            # attendee_json = event["attendee"]
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
        print(f"An SQLAlchemy error occurred: {e}")
        db.rollback()
        raise abort(500, description="Internal Server Error")


def list_events(username):
    """Lists all events"""
    try:
        user = db.query(User).filter(User.email == username).first()
        if not user:
            raise abort(404, description="User not found")

        events = db.query(Event).filter(Event.user_id == user.id).all()

        return [event.to_dict() for event in events]  # Convert to list of dictionaries

    except Exception as e:
        print(f"An error occurred: {e}")
        raise abort(500, description="Internal Server Error")

def update_event(event):
    """Updating Event Details. (Currently working on this; will be completed in the next comment)"""
    try:
        event_detail = db.query(Event).filter(Event.id==event['id'],Event.user_id==event['user_id']).first()
        if not event_detail:
            raise abort(404, description="Event not found")
        event_detail.event_date = event['event_date']
        db.commit()
        return {"message": "Event details updated successfully"}, 200
    except Exception as e:
        raise abort(500, description="Internal Server Error")
