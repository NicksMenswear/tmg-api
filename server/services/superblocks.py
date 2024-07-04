import json
import logging
import os
from abc import ABC, abstractmethod

from server.controllers.util import http
from server.services import ServiceError

logger = logging.getLogger(__name__)


SUPERBLOCKS_ORDER_WEBHOOK_API_URL = os.getenv("SUPERBLOCKS_ORDER_WEBHOOK_API_URL")


class AbstractSuperblocksService(ABC):
    @abstractmethod
    def order_created_webhook(self, body):
        pass


class FakeSuperblocksService(AbstractSuperblocksService):
    def order_created_webhook(self, body):
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

    def order_created_webhook(self, body):
        status, body = self.api_request("POST", SUPERBLOCKS_ORDER_WEBHOOK_API_URL, body)

        if status >= 400:
            raise ServiceError(f"Failed to create order in Superblocks: {body}")

        return body
