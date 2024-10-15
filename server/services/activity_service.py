import hashlib
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime

from server.database.database_manager import db
from server.database.models import Activity
from server.flask_app import FlaskApp
from server.services import ServiceError

logger = logging.getLogger(__name__)


def suppress_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception("Exception suppressed in %s: %s", func.__name__, str(e))

    return wrapper


class AbstractActivityService(ABC):
    @abstractmethod
    def generic(self, email, type, data):
        pass


class FakeActivityService(AbstractActivityService):
    def __init__(self):
        self.contacts = []

    def generic(self, email, type, data):
        pass


class ActivityService(AbstractActivityService):
    @suppress_exceptions
    def generic(self, email, type, data):
        user_service = FlaskApp.current().user_service
        user = user_service.get_user_by_email(email)
        data_md5 = hashlib.md5(json.dumps(data).encode("utf-8")).hexdigest()

        try:
            activity = Activity(
                user_id=user.id,
                type=type,
                data=data,
                data_md5=data_md5,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.session.add(activity)
            db.session.commit()

        except Exception as e:
            raise ServiceError("Failed to save activity", e)

        count = Activity.query.filter(
            Activity.user_id == user.id,
            Activity.type == type,
            Activity.data_md5 == data_md5,
        ).count()
        return {"count": count}
