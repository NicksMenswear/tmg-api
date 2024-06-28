import logging
import uuid

from server.database.database_manager import db
from server.database.models import Size
from server.services.user import UserService
from server.services import ServiceError

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class SizeService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def create(self, data: dict) -> uuid.UUID:
        try:
            size = Size(user_id=data["user_id"], data=data["data"])

            db.session.add(size)
            db.session.commit()
            db.session.refresh(size)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to save size data", e)

        self.user_service.set_size(data["user_id"])

        return size.id
