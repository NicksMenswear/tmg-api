import os
from abc import ABC, abstractmethod

from server.controllers.util import http
from server.services import ServiceError
from server.models.user_model import CreateUserModel

ACTIVECAMPAIGN_API_URL = os.getenv("ACTIVECAMPAIGN_API_URL")
ACTIVECAMPAIGN_API_KEY = os.getenv("ACTIVECAMPAIGN_API_KEY")


class AbstractActiveCampaignService(ABC):
    @abstractmethod
    def create_contact(self, user: CreateUserModel):
        pass


class FakeActiveCampaignService(AbstractActiveCampaignService):
    def create_contact(self, user: CreateUserModel):
        pass


class ActiveCampaignService(AbstractActiveCampaignService):
    def create_contact(self, user: CreateUserModel):
        body = {
            "contact": {
                "email": user.email,
                "firstName": user.first_name,
                "lastName": user.last_name,
            }
        }
        self._activecampaign_request("POST", "contacts", body)

    def _activecampaign_request(self, method, path, json):
        headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
            "Api-Token": ACTIVECAMPAIGN_API_KEY,
        }
        response = http(
            method,
            f"{ACTIVECAMPAIGN_API_URL}/api/3/{path}",
            headers=headers,
            json=json,
        )
        if response.status == 422:
            # Ignore duplicates
            return
        if response.status >= 400:
            raise ServiceError(f"Error using ActiveCampaign: {response.data.decode('utf-8')}")
