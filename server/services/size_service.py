import logging
import uuid
from typing import Optional

from server.database.database_manager import db
from server.database.models import Size
from server.models.size_model import SizeModel, CreateSizeRequestModel
from server.services import ServiceError
from server.services.measurement_service import MeasurementService
from server.services.order_service import (
    OrderService,
)
from server.services.user_service import UserService

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class SizeService:
    def __init__(self, user_service: UserService, measurement_service: MeasurementService, order_service: OrderService):
        self.user_service = user_service
        self.measurement_service = measurement_service
        self.order_service = order_service

    def get_latest_size_for_user(self, user_id: uuid.UUID) -> Optional[SizeModel]:
        size = Size.query.filter(Size.user_id == user_id).order_by(Size.created_at.desc()).first()

        if not size:
            return None

        return SizeModel.model_validate(size)

    def create_size(self, create_size_request: CreateSizeRequestModel) -> SizeModel:
        try:
            size = Size(
                user_id=create_size_request.user_id,
                measurement_id=create_size_request.measurement_id,
                data=create_size_request.data,
            )

            db.session.add(size)
            db.session.commit()
            db.session.refresh(size)

            size_model = SizeModel.model_validate(size)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to save size data", e)

        self.user_service.set_size(size.user_id)

        return size_model
