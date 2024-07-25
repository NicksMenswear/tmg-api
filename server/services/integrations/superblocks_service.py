import json
import logging
from abc import ABC

from server.controllers.util import http

logger = logging.getLogger(__name__)


class AbstractSuperblocksService(ABC):
    pass


class FakeSuperblocksService(AbstractSuperblocksService):
    pass


class SuperblocksService(AbstractSuperblocksService):
    def api_request(self, method, endpoint, body=None):
        response = http(
            method,
            endpoint,
            json=body,
            headers={"Content-Type": "application/json"},
        )

        return response.status, json.loads(response.data.decode("utf-8"))
