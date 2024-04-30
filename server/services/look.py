import uuid

from server.database.database_manager import db
from server.database.models import Look
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.base import BaseService
from server.services.attendee import AttendeeService
from server.services.role import RoleService
from server.services.user import UserService


class LookService(BaseService):
    def __init__(self):
        super().__init__()
        self.user_service = UserService()
        self.role_service = RoleService()
        self.attendee_service = AttendeeService()

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
        user = self.user_service.get_user_by_email(look_data["email"])

        if not user:
            raise NotFoundError("User not found")

        look = self.get_look_by_id(look_data["look_id"])

        if not look:
            raise NotFoundError("Look not found")

        role = self.role_service.get_role_by_look_id_and_event_id(look.id, look.event_id)

        if not role:
            raise NotFoundError("Role not found")

        attendee = self.attendee_service.get_attendee_by_id(look_data["attendee_id"])

        if not attendee:
            raise NotFoundError("Attendee not found")

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

            new_role = self.role_service.create_role(
                role_name=role.role_name, event_id=role.event_id, look_id=new_look.id
            )

            attendee.role = new_role.id

            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to update look.", e)

        return new_look
