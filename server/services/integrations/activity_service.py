import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from server.controllers.util import http
from server.services import ServiceError

logger = logging.getLogger(__name__)


class AbstractActivityService(ABC):
    @abstractmethod
    def page_view(
        self,
        user_id,
        page_name,
    ):
        pass


class FakeActivityService(AbstractActivityService):
    def __init__(self):
        self.contacts = []

    def page_view(
        self,
        user_id,
        page_name,
    ):
        pass


class ActiveCampaignService(AbstractActivityService):
    def page_view(
        self,
        user_id,
        page_name,
    ):
        pass
