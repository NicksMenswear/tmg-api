import os
from abc import ABC, abstractmethod

from server.controllers.util import http
from server.services import ServiceError
from server.services.shopify import AbstractShopifyService

AC_URL = os.getenv("ACTIVE_CAMPAIGN_URL")
AC_API_KEY = os.getenv("ACTIVE_CAMPAIGN_API_KEY")
AC_FIELD_IDS = {"shopify_customer_id": 118, "shopify_activation_url": 117, "shopify_event_url": 119}
AC_AUTOMATION_IDS = {
    "activation": 202,
}


class AbstractEmailService(ABC):
    @abstractmethod
    def send_activation_url(self, email, shopify_customer_id):
        pass


class FakeEmailService(AbstractEmailService):
    def send_activation_url(self, email, shopify_customer_id):
        pass


class EmailService(AbstractEmailService):
    def __init__(self, shopify_service: AbstractShopifyService):
        self.shopify_service = shopify_service
        self._api_url = f"{AC_URL}/api/3"
        self._api_headers = {"Api-Token": AC_API_KEY, "Content-Type": "application/json"}

    def _sync_ac_contact(self, email, first_name, last_name, shopify_customer_id, activation_url=None, event_url=None):
        contact_data = {
            "contact": {
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "fieldValues": [
                    {"field": AC_FIELD_IDS["shopify_customer_id"], "value": shopify_customer_id},
                    {"field": AC_FIELD_IDS["shopify_activation_url"], "value": activation_url}
                    if activation_url
                    else {},
                    {"field": AC_FIELD_IDS["shopify_event_url"], "value": event_url} if event_url else {},
                ],
            }
        }

        response = http("POST", f"{self._api_url}/contact/sync", headers=self._api_headers, json=contact_data)
        if response.status_code > 400:
            raise ServiceError(f"Error interacting with email service.")

        contact_id = response.json()["contact"]["id"]
        return contact_id

    def send_activation_url(self, email, first_name, last_name, shopify_customer_id):
        activation_url = self.shopify_service.get_activation_url(shopify_customer_id)
        ac_contact_id = self._sync_ac_contact(email, first_name, last_name, shopify_customer_id, activation_url)
        url = f"{self._api_url}/contactAutomations"
        data = {"contactAutomation": {"contact": ac_contact_id, "automation": AC_AUTOMATION_IDS["activation"]}}
        response = http("POST", url, headers=self._api_headers, json=data)
        if response.status_code > 400:
            raise ServiceError(f"Error triggering email automation.")
