import os
from abc import ABC, abstractmethod

from server.controllers.util import http
from server.services import ServiceError
from server.models.user_model import UserModel
from server.services.shopify import AbstractShopifyService

POSTMARK_API_URL = os.getenv("POSTMARK_API_URL")
POSTMARK_API_KEY = os.getenv("POSTMARK_API_KEY")
FROM_EMAIL = "info@themoderngroom.com"


class PostmarkTemplates:
    ACTIVATION = 36199819
    INVITE = 36201238


class AbstractEmailService(ABC):
    @abstractmethod
    def send_activation_email(self, user: UserModel):
        pass

    @abstractmethod
    def send_invite_email(self, user: UserModel):
        pass


class FakeEmailService(AbstractEmailService):
    def send_activation_email(self, user: UserModel):
        pass

    def send_invite_email(self, user: UserModel):
        pass


class EmailService(AbstractEmailService):
    def __init__(self, shopify_service: AbstractShopifyService):
        self.shopify_service = shopify_service

    def _postmark_request(self, method, path, json):
        headers = {"X-Postmark-Server-Token": POSTMARK_API_KEY}
        response = http(
            method,
            f"{POSTMARK_API_URL}/{path}",
            headers=headers,
            json=json,
        )
        if response.status >= 400:
            raise ServiceError(f"Error sending email: {response.data.decode('utf-8')}")

    def send_activation_email(self, user: UserModel):
        activation_url = self.shopify_service.get_activation_url(user.shopify_id)
        body = {
            "From": FROM_EMAIL,
            "To": user.email,
            "TemplateId": PostmarkTemplates.ACTIVATION,
            "TemplateModel": {"first_name": user.first_name, "shopify_url": activation_url},
        }
        self._postmark_request("POST", "email/withTemplate", body)

    def send_invite_email(self, user: UserModel, with_activation=False):
        if with_activation:
            shopify_url = self.shopify_service.get_activation_url(user.shopify_id)
            button_text = "Activate Account & Get Started"
        else:
            shopify_url = self.shopify_service.get_login_url()
            button_text = "Get Started"
        body = {
            "From": FROM_EMAIL,
            "To": user.email,
            "TemplateId": PostmarkTemplates.INVITE,
            "TemplateModel": {"first_name": user.first_name, "shopify_url": shopify_url, "button_text": button_text},
        }
        self._postmark_request("POST", "email/withTemplate", body)
