import logging
import uuid
from typing import Optional

from server.database.database_manager import db
from server.database.models import Size
from server.models.size_model import SizeModel, CreateSizeRequestModel
from server.services import ServiceError
from server.services.measurement import MeasurementService
from server.services.order import (
    ORDER_STATUS_PENDING_MEASUREMENTS,
    MAX_DAYS_TO_LOOK_UP_FOR_PENDING_MEASUREMENTS,
    OrderService,
)
from server.services.user import UserService

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

        return SizeModel.from_orm(size)

    def create_size(self, create_size_request: CreateSizeRequestModel) -> SizeModel:
        try:
            size = Size(user_id=create_size_request.user_id, data=create_size_request.data)

            db.session.add(size)
            db.session.commit()
            db.session.refresh(size)

            size_model = SizeModel.from_orm(size)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to save size data", e)

        self.user_service.set_size(size.user_id)

        measurement_model = self.measurement_service.get_latest_measurement_for_user(size.user_id)

        orders = self.order_service.get_orders_by_status_and_not_older_then_days(
            ORDER_STATUS_PENDING_MEASUREMENTS, MAX_DAYS_TO_LOOK_UP_FOR_PENDING_MEASUREMENTS
        )

        for order in orders:
            self.order_service.update_order_skus_according_to_measurements(order, size_model, measurement_model)

        return size_model
