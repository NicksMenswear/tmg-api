import logging
import uuid

from server.database.database_manager import db
from server.database.models import Sizing
from server.services import ServiceError

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class SizingService:
    def create(self, data: dict) -> uuid.UUID:
        try:
            sizing = Sizing(data=data)

            db.session.add(sizing)
            db.session.commit()
            db.session.refresh(sizing)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to save sizing data", e)

        return sizing.id
