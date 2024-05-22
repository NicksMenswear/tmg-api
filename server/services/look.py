import uuid

from server.database.database_manager import db
from server.database.models import Look, Event, Attendee, User
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.user import UserService


class LookService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def get_look_by_id(self, look_id):
        return Look.query.filter(Look.id == look_id).first()

    def get_events_for_look(self, look_id):
        return Event.query.join(Attendee, Event.id == Attendee.event_id).filter(Attendee.look_id == look_id).all()

    def create_look(self, look_data):
        look = Look.query.filter(Look.look_name == look_data["look_name"], Look.user_id == look_data["user_id"]).first()

        if look:
            raise DuplicateError("Look already exists with that name.")

        try:
            look = Look(
                id=uuid.uuid4(),
                look_name=look_data.get("look_name"),
                user_id=look_data.get("user_id"),
                product_specs=look_data.get("product_specs"),
            )

            db.session.add(look)
            db.session.commit()
            db.session.refresh(look)
        except Exception as e:
            raise ServiceError("Failed to create look.", e)

        return look

    def update_look(self, look_id, look_data):
        look = Look.query.filter(Look.id == look_id).first()

        if not look:
            raise NotFoundError("Look not found")

        user = User.query.filter_by(id=look_data["user_id"]).first()

        if not user:
            raise NotFoundError("User not found")

        existing_look = Look.query.filter(
            Look.look_name == look_data["look_name"], Look.user_id == user.id, Look.id != look_id
        ).first()

        if existing_look:
            raise DuplicateError("Look already exists with that name.")

        try:
            look.look_name = look_data.get("look_name")
            look.product_specs = look_data.get("product_specs")

            db.session.commit()
            db.session.refresh(look)
        except Exception as e:
            raise ServiceError("Failed to update look.", e)

        return look

    def delete_look(self, look_id):
        look = Look.query.filter(Look.id == look_id).first()

        if not look:
            raise NotFoundError("Look not found")

        try:
            db.session.delete(look)
            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to delete look.", e)
