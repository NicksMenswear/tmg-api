import logging
import uuid

from server.database.database_manager import db
from server.database.models import Size
from server.models.size_model import SizeModel, CreateSizeRequestModel
from server.services import ServiceError
from server.services.attendee_service import AttendeeService
from server.services.integrations.shopify_service import AbstractShopifyService
from server.services.measurement_service import MeasurementService
from server.services.order_service import OrderService
from server.services.user_service import UserService

logger = logging.getLogger(__name__)


class SizeService:
    def __init__(
        self,
        user_service: UserService,
        attendee_service: AttendeeService,
        measurement_service: MeasurementService,
        order_service: OrderService,
        shopify_service: AbstractShopifyService,
    ):
        self.user_service = user_service
        self.attendee_service = attendee_service
        self.measurement_service = measurement_service
        self.order_service = order_service
        self.shopify_service = shopify_service

    @staticmethod
    def get_latest_size_for_user(user_id: uuid.UUID) -> SizeModel | None:
        size = Size.query.filter(Size.user_id == user_id).order_by(Size.created_at.desc()).first()

        if not size:
            return None

        return SizeModel.model_validate(size)

    @staticmethod
    def get_latest_size_for_user_by_email(email: str) -> SizeModel | None:
        size = Size.query.filter(Size.email == email).order_by(Size.created_at.desc()).first()

        if not size:
            return None

        return SizeModel.model_validate(size)

    def create_size(self, create_size_request: CreateSizeRequestModel) -> SizeModel:
        try:
            size = Size(
                user_id=create_size_request.user_id,
                email=create_size_request.email,
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

        self.attendee_service.mark_attendees_as_sized_by_user_id_or_email(size.user_id, size.email)
        self.user_service.update_customer_with_latest_sizing(size.user_id, size.email, size.created_at.isoformat())

        return size_model

    @staticmethod
    def associate_sizing_that_has_email_with_user(email: str, user_id: uuid.UUID):
        sizes = Size.query.filter(Size.email == email, Size.user_id == None).all()

        if not sizes:
            return

        for size in sizes:
            size.user_id = user_id

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to associate sizes with user", e)
