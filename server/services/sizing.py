import logging
import uuid

from server.database.database_manager import db
from server.database.models import Sizing
from server.services import ServiceError

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class SizingService:
    def store(self, data: dict) -> uuid.UUID:
        try:
            sizing = Sizing(data=data)

            db.session.add(sizing)
            db.session.commit()
            db.session.refresh(sizing)
        except Exception as e:
            logger.error(f"Failed to store sizing data: {e}: {data}")
            db.session.rollback()
            raise ServiceError("Failed to store sizing data")

        return sizing.id
