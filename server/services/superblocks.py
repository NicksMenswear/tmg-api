import json
import logging
import os
import uuid
from abc import ABC, abstractmethod

from server.controllers.util import http
from server.services import ServiceError

logger = logging.getLogger(__name__)


SUPERBLOCKS_ORDER_WEBHOOK_API_URL = os.getenv("SUPERBLOCKS_ORDER_WEBHOOK_API_URL")


class AbstractSuperblocksService(ABC):
    @abstractmethod
    def generate_order_number(self):
        return str(uuid.uuid4())


class FakeSuperblocksService(AbstractSuperblocksService):
    def generate_order_number(self):
        return str(uuid.uuid4())


class SuperblocksService(AbstractSuperblocksService):
    def api_request(self, method, endpoint, body=None):
        response = http(
            method,
            endpoint,
            json=body,
            headers={"Content-Type": "application/json"},
        )

        return response.status, json.loads(response.data.decode("utf-8"))

    def generate_order_number(self):
        status, body = self.api_request("POST", SUPERBLOCKS_ORDER_WEBHOOK_API_URL)

        if status >= 400:
            raise ServiceError(f"Failed to generate order number. {body}")

        return body.get("output", {}).get("result")
