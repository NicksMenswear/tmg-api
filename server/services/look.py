import uuid

from server.database.models import Event, Look
from server.services import ServiceError, DuplicateError
from server.services.base import BaseService


class LookService(BaseService):
    def __init__(self, session_factory):
        super().__init__(session_factory)

    def get_all_looks(self):
        with self.session_factory() as db:
            return db.query(Look).all()

    def get_looks_for_user(self, user_id):
        with self.session_factory() as db:
            return db.query(Look).filter(Look.user_id == user_id).all()

    def get_look_by_id_and_user(self, look_id, user_id):
        with self.session_factory() as db:
            return db.query(Look).filter(Look.id == look_id, Look.user_id == user_id).first()

    def create_look(self, **look_data):
        with self.session_factory() as db:
            look = (
                db.query(Look)
                .filter(Look.look_name == look_data["look_name"], Look.user_id == look_data["user_id"])
                .first()
            )

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

                db.add(look)
                db.commit()
                db.refresh(look)
            except Exception as e:
                raise ServiceError("Failed to create look.", e)

            return look
