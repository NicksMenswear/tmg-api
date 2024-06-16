import uuid
from datetime import datetime
from typing import List

from server.database.database_manager import db
from server.database.models import Look, Attendee
from server.models.look_model import CreateLookModel, LookModel, UpdateLookModel
from server.services import ServiceError, DuplicateError, NotFoundError, BadRequestError
from server.services.user import UserService


# noinspection PyMethodMayBeStatic
class LookService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def get_look_by_id(self, look_id: uuid.UUID) -> LookModel:
        db_look = Look.query.filter(Look.id == look_id).first()

        if not db_look:
            raise NotFoundError("Look not found")

        return LookModel.from_orm(db_look)

    def get_looks_by_user_id(self, user_id: uuid.UUID) -> List[LookModel]:
        return [
            LookModel.from_orm(look)
            for look in Look.query.filter(Look.user_id == user_id, Look.is_active).order_by(Look.created_at.asc()).all()
        ]

    def create_look(self, create_look: CreateLookModel) -> LookModel:
        db_look: Look = Look.query.filter(
            Look.name == create_look.name, Look.user_id == create_look.user_id, Look.is_active
        ).first()

        if db_look:
            raise DuplicateError("Look already exists with that name.")

        try:
            db_look = Look(
                id=uuid.uuid4(),
                name=create_look.name,
                user_id=create_look.user_id,
                product_specs=create_look.product_specs,
                is_active=create_look.is_active,
            )

            db.session.add(db_look)
            db.session.commit()
            db.session.refresh(db_look)
        except Exception as e:
            raise ServiceError("Failed to create look.", e)

        return LookModel.from_orm(db_look)

    def update_look(self, look_id: uuid.UUID, update_look: UpdateLookModel) -> LookModel:
        db_look = Look.query.filter(Look.id == look_id).first()

        if not db_look:
            raise NotFoundError("Look not found")

        existing_look = Look.query.filter(
            Look.name == update_look.name, Look.user_id == db_look.user_id, Look.id != look_id
        ).first()

        if existing_look:
            raise DuplicateError("Look already exists with that name.")

        try:
            db_look.name = update_look.name
            db_look.product_specs = update_look.product_specs
            db_look.updated_at = datetime.now()

            db.session.commit()
            db.session.refresh(db_look)
        except Exception as e:
            raise ServiceError("Failed to update look.", e)

        return LookModel.from_orm(db_look)

    def delete_look(self, look_id: uuid.UUID) -> None:
        look = Look.query.filter(Look.id == look_id).first()

        if not look:
            raise NotFoundError("Look not found")

        num_attendees = Attendee.query.filter(Attendee.look_id == look_id, Attendee.is_active).count()

        if num_attendees > 0:
            raise BadRequestError("Can't delete look associated to attendee")

        try:
            look.is_active = False
            look.updated_at = datetime.now()

            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to delete look.", e)
