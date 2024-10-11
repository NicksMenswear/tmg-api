import json
from abc import ABC, abstractmethod

from server.controllers.util import http


class AbstractSuperblocksService(ABC):
    @abstractmethod
    def api_request(self, method, endpoint, body=None):
        pass


# noinspection PyUnusedLocal
class FakeSuperblocksService(AbstractSuperblocksService):
    def api_request(self, method, endpoint, body=None):
        return 200, {}


class SuperblocksService(AbstractSuperblocksService):
    def api_request(self, method, endpoint, body=None):
        response = http(
            method,
            endpoint,
            json=body,
            headers={"Content-Type": "application/json"},
        )

        return response.status, json.loads(response.data.decode("utf-8"))
