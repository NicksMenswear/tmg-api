import uuid

from server.database.database_manager import db
from server.database.models import Look, Event
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.user import UserService


class LookService:
    def __init__(self):
        self.user_service = UserService()

    def get_all_looks(self):
        return Look.query.all()

    def get_looks_by_event_id(self, event_id):
        return Look.query.filter(Look.event_id == event_id).all()

    def get_look_by_id(self, look_id):
        return Look.query.filter(Look.id == look_id).first()

    def get_looks_for_user(self, user_id):
        return Look.query.filter(Look.user_id == user_id).all()

    def get_look_by_id_and_user(self, look_id, user_id):
        return Look.query.filter(Look.id == look_id, Look.user_id == user_id).first()

    def create_look(self, look_data):
        look = Look.query.filter(Look.look_name == look_data["look_name"], Look.user_id == look_data["user_id"]).first()

        if look:
            raise DuplicateError("Look already exists with that name.")

        try:
            look = Look(
                id=uuid.uuid4(),
                look_name=look_data["look_name"],
                event_id=look_data.get("event_id"),
                user_id=look_data.get("user_id"),
                product_specs=look_data.get("product_specs"),
                product_final_image=look_data.get("product_final_image"),
            )

            db.session.add(look)
            db.session.commit()
            db.session.refresh(look)
        except Exception as e:
            raise ServiceError("Failed to create look.", e)

        return look

    def update_look(self, look_data):
        look = Look.query.filter(Look.id == look_data["id"]).first()

        if not look:
            raise NotFoundError("Look not found")

        user = self.user_service.get_user_by_id(look_data["user_id"])

        if not user:
            raise NotFoundError("User not found")

        event = Event.query.filter(Event.id == look_data["event_id"]).first()

        if not event:
            raise NotFoundError("Event not found")

        try:
            new_look = self.create_look(
                look_data=dict(
                    id=uuid.uuid4(),
                    look_name=look_data["look_name"],
                    event_id=look_data.get("event_id"),
                    user_id=look_data.get("user_id"),
                    product_specs=look_data.get("product_specs"),
                    product_final_image=look_data.get("product_final_image"),
                )
            )

            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to update look.", e)

        return new_look
