import logging
import uuid
from typing import Optional

from server.database.database_manager import db
from server.database.models import Measurement
from server.models.measurement_model import MeasurementModel, CreateMeasurementsRequestModel
from server.services import ServiceError

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class MeasurementService:
    def get_latest_measurement_for_user(self, user_id: uuid.UUID) -> Optional[MeasurementModel]:
        measurement = (
            Measurement.query.filter(Measurement.user_id == user_id).order_by(Measurement.created_at.desc()).first()
        )

        if not measurement:
            return None

        return MeasurementModel.from_orm(measurement)

    def create_measurement(self, create_measurement_request: CreateMeasurementsRequestModel) -> MeasurementModel:
        try:
            measurement = Measurement(user_id=create_measurement_request.user_id, data=create_measurement_request.data)

            db.session.add(measurement)
            db.session.commit()
            db.session.refresh(measurement)

            measurement_model = MeasurementModel.from_orm(measurement)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to save measurement data", e)

        return measurement_model
