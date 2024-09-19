from datetime import datetime
from functools import wraps
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from server.controllers.util import http
from server.flask_app import FlaskApp
from server.services import ServiceError
from logs import log_activity_wrapper

logger = logging.getLogger(__name__)


def suppress_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception("Exception suppressed in %s", func.__name__)

    return wrapper


class AbstractActivityService(ABC):
    @abstractmethod
    def page_view(
        self,
        email,
        page_name,
    ):
        pass


class FakeActivityService(AbstractActivityService):
    def __init__(self):
        self.contacts = []

    def page_view(
        self,
        email,
        page_name,
    ):
        pass


class ActivityService(AbstractActivityService):
    @log_activity_wrapper
    @suppress_exceptions
    def page_view(
        self,
        email,
        page_name,
    ):
        user_service = FlaskApp.current().user_service
        shopify_service = FlaskApp.current().shopify_service

        user = user_service.get_user_by_email(email)
        shopify_service.append_customer_tags(user.shopify_id, [f"page_view_{page_name}"])
