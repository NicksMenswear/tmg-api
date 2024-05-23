import uuid

from server.database.database_manager import db
from server.database.models import Look, Event, Attendee
from server.models.look_model import CreateLookModel, LookModel, UpdateLookModel
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.user import UserService


class LookService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def get_look_by_id(self, look_id: uuid.UUID) -> LookModel:
        db_look = Look.query.filter(Look.id == look_id).first()

        if not db_look:
            raise NotFoundError("Look not found")

        return LookModel.from_orm(db_look)

    def get_looks_by_user_id(self, user_id: uuid.UUID) -> list[LookModel]:
        return [LookModel.from_orm(look).to_response() for look in Look.query.filter(Look.user_id == user_id).all()]

    # TODO: pydantify
    def get_events_for_look(self, look_id):
        return Event.query.join(Attendee, Event.id == Attendee.event_id).filter(Attendee.look_id == look_id).all()

    def create_look(self, create_look: CreateLookModel) -> LookModel:
        db_look: Look = Look.query.filter(
            Look.look_name == create_look.look_name, Look.user_id == create_look.user_id
        ).first()

        if db_look:
            raise DuplicateError("Look already exists with that name.")

        try:
            db_look = Look(
                id=uuid.uuid4(),
                look_name=create_look.look_name,
                user_id=create_look.user_id,
                product_specs=create_look.product_specs,
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
            Look.look_name == update_look.look_name, Look.user_id == db_look.user_id, Look.id != look_id
        ).first()

        if existing_look:
            raise DuplicateError("Look already exists with that name.")

        try:
            db_look.look_name = update_look.look_name
            db_look.product_specs = update_look.product_specs

            db.session.commit()
            db.session.refresh(db_look)
        except Exception as e:
            raise ServiceError("Failed to update look.", e)

        return LookModel.from_orm(db_look)

    def delete_look(self, look_id: uuid.UUID):
        look = Look.query.filter(Look.id == look_id).first()

        if not look:
            raise NotFoundError("Look not found")

        try:
            db.session.delete(look)
            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to delete look.", e)
