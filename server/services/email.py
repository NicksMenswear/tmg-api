import os
from abc import ABC, abstractmethod

from server.controllers.util import http
from server.services import ServiceError
from server.services.shopify import AbstractShopifyService

POSTMARK_API_URL = os.getenv("POSTMARK_API_URL")
POSTMARK_API_KEY = os.getenv("ACTIVE_CAMPAIGN_API_KEY")
FROM_EMAIL = "info@themoderngroom.com"


class PostmarkTemplates:
    ACTIVATION = 36199819
    INVITE = 123


class AbstractEmailService(ABC):
    @abstractmethod
    def send_activation_email(self, email, shopify_customer_id):
        pass

    @abstractmethod
    def send_invite_email(self, email, shopify_customer_id):
        pass


class FakeEmailService(AbstractEmailService):
    def send_activation_url(self, email, shopify_customer_id):
        pass

    def send_invite_email(self, email, shopify_customer_id):
        pass


class EmailService(AbstractEmailService):
    def __init__(self, shopify_service: AbstractShopifyService):
        self.shopify_service = shopify_service

    def _postmark_request(self, method, path, json):
        headers = {"X-Postmark-Server-Token": POSTMARK_API_KEY, "Content-Type": "application/json"}
        response = http(
            method,
            f"{POSTMARK_API_URL}/{path}",
            headers=headers,
            json=json,
        )
        if response.status_code >= 400:
            raise ServiceError(f"Error sending email: {response.text}")

    def send_activation_url(self, email, first_name, last_name, shopify_customer_id):
        activation_url = self.shopify_service.get_activation_url(shopify_customer_id)
        body = {
            "From": FROM_EMAIL,
            "To": email,
            "TemplateId": PostmarkTemplates.ACTIVATION,
            "TemplateModel": {"first_name": first_name, "shopify_url": activation_url},
        }
        self._postmark_request("POST", "email/withTemplate", body)

    def send_invite_email(self, email, first_name, last_name, shopify_customer_id):
        pass
