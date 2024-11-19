import logging
import uuid

from sqlalchemy.sql.elements import or_

from server.database.database_manager import db
from server.database.models import Measurement
from server.flask_app import FlaskApp
from server.models.measurement_model import MeasurementModel, CreateMeasurementsRequestModel
from server.services import ServiceError, NotFoundError

logger = logging.getLogger(__name__)


class MeasurementService:
    @staticmethod
    def get_measurement_by_id(measurement_id: uuid.UUID) -> MeasurementModel | None:
        measurement = Measurement.query.get(measurement_id)

        if not measurement:
            return None

        return MeasurementModel.model_validate(measurement)

    @staticmethod
    def get_latest_measurement_for_user_by_id_or_email(
        user_id: uuid.UUID = None, email: str = None
    ) -> MeasurementModel | None:
        if user_id is None and email is None:
            return None

        measurement = None

        if user_id is not None and email is None:
            try:
                user = FlaskApp.current().user_service.get_user_by_id(user_id)
            except NotFoundError:
                return None

            email = user.email

            measurement = (
                Measurement.query.filter(or_(Measurement.user_id == user_id, Measurement.email == email))  # type: ignore
                .order_by(Measurement.created_at.desc())
                .first()
            )
        elif email is not None and user_id is None:
            try:
                user = FlaskApp.current().user_service.get_user_by_email(email)
            except NotFoundError:
                user = None

            if user is None:
                measurement = (
                    Measurement.query.filter(Measurement.email == email).order_by(Measurement.created_at.desc()).first()
                )
            else:
                measurement = (
                    Measurement.query.filter(or_(Measurement.user_id == user.id, Measurement.email == email))  # type: ignore
                    .order_by(Measurement.created_at.desc())
                    .first()
                )
        elif email is not None and user_id is not None:
            measurement = (
                Measurement.query.filter(or_(Measurement.user_id == user_id, Measurement.email == email))  # type: ignore
                .order_by(Measurement.created_at.desc())
                .first()
            )

        if not measurement:
            return None

        return MeasurementModel.model_validate(measurement)

    @staticmethod
    def create_measurement(create_measurement_request: CreateMeasurementsRequestModel) -> MeasurementModel:
        try:
            measurement = Measurement(
                user_id=create_measurement_request.user_id,
                email=create_measurement_request.email,
                data=create_measurement_request.data,
            )

            db.session.add(measurement)
            db.session.commit()
            db.session.refresh(measurement)

            measurement_model = MeasurementModel.model_validate(measurement)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to save measurement data", e)

        return measurement_model
