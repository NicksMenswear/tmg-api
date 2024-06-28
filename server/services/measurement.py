import logging
import uuid

from server.database.database_manager import db
from server.database.models import Measurement
from server.services import ServiceError

logger = logging.getLogger(__name__)


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
