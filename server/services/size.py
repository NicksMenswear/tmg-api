import logging
import uuid

from server.database.database_manager import db
from server.database.models import Size, Measurement
from server.services.user import UserService
from server.services import ServiceError

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class SizeService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def create(self, user_id: uuid.UUID, data: dict) -> uuid.UUID:
        try:
            size = Size(user_id=user_id, data=data)

            db.session.add(size)
            db.session.commit()
            db.session.refresh(size)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to save size data", e)

        self.user_service.set_size(user_id)

        return size.id


# noinspection PyMethodMayBeStatic
class MeasurementService:
    def create(self, user_id: uuid.UUID, data: dict) -> uuid.UUID:
        try:
            measurement = Measurement(user_id=user_id, data=data)

            db.session.add(measurement)
            db.session.commit()
            db.session.refresh(measurement)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to save measurement data", e)

        return measurement.id
