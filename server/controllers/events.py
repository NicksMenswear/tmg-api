import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from server.database.models import Event, User, Look, Role, Attendee
from server.database.database_manager import get_database_session
from sqlalchemy import exists, text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
import uuid
from server.controllers.hmac_1 import hmac_verification
from urllib.parse import unquote


db = get_database_session()


@hmac_verification()
def create_event(event):
    """Create event"""
    try:
        user = db.query(User).filter(User.email == event["email"]).first()
        if not user:
            return "User not found", 204
        existing_event = db.query(
            exists()
            .where(Event.event_name == event["event_name"])
            .where(Event.event_date == event["event_date"])
            .where(Event.user_id == user.id)
            .where(Event.is_active == True)
        ).scalar()

        if existing_event:
            return "event with the same detail already exists!", 400

        else:
            event_id = uuid.uuid4()
            new_event = Event(
                id=event_id, event_name=event["event_name"], event_date=event["event_date"], user_id=user.id
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
    username = unquote(username)
    try:
        user = db.query(User).filter(User.email == username).first()
        if not user:
            return "User not found", 204
        formatted_data = []
        events = db.query(Event).filter(Event.user_id == user.id, Event.is_active == True).all()
        for event in events:
            roles = db.query(Role).filter(Role.event_id == event.id).all()
            data = {
                "id": event.id,
                "event_name": event.event_name,
                "event_date": str(event.event_date),
                "user_id": str(event.user_id),
                "looks": [],
            }
            for role in roles:
                look = db.query(Look).filter(Look.id == role.look_id).first()
                look_data = {
                    "id": look.id,
                    "look_name": look.look_name,
                    "user_id": look.user_id,
                    "product_specs": look.product_specs,
                    "product_final_image": look.product_final_image,
                }
                data["looks"].append(look_data)
            formatted_data.append(data)

        # return [event.to_dict() for event in events]  # Convert to list of dictionaries
        return formatted_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def list_events_attendees(email):
    """Lists all events for a singal Attendee"""
    email = unquote(email)
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return "User not found", 200
        formatted_data = []
        attendees = db.query(Attendee).filter(Attendee.attendee_id == user.id).all()
        for attendee in attendees:
            event = db.query(Event).filter(Event.id == attendee.event_id, Event.is_active == True).first()
            if event is None:
                continue
            role = db.query(Role).filter(Role.id == attendee.role).first()

            if role:
                look = db.query(Look).filter(Look.id == role.look_id).first()

                if look is None:
                    look_data = {}
                else:
                    look_data = {
                        "id": look.id,
                        "look_name": look.look_name,
                        "product_specs": look.product_specs,
                        "product_final_image": look.product_final_image,
                    }
                data = {
                    "event_id": event.id,
                    "event_name": event.event_name,
                    "event_date": str(event.event_date),
                    "user_id": str(event.user_id),
                    "look_data": look_data,
                }
                formatted_data.append(data)
            else:
                look_data = {}
                data = {
                    "event_id": event.id,
                    "event_name": event.event_name,
                    "event_date": str(event.event_date),
                    "user_id": str(event.user_id),
                    "look_data": look_data,
                }
                formatted_data.append(data)

        return formatted_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def update_event(event):
    """Updating Event Details."""
    try:
        event_detail = db.query(Event).filter(Event.id == event["id"], Event.user_id == event["user_id"]).first()
        if not event_detail:
            return "Event not found", 200
        event_detail.event_date = event["event_date"]
        db.commit()
        return "Event details updated successfully", 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def soft_delete_event(event):
    """Deleting Event Details."""
    try:
        event_detail = db.query(Event).filter(Event.id == event["event_id"]).first()
        if not event_detail:
            return "Event not found", 200
        event_detail.is_active = event["is_active"]
        db.commit()
        return "Event details deleted successfully", 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
