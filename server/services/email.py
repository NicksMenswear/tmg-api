import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    def send_invites_batch(self, users: list[UserModel]):
        pass


class FakeEmailService(AbstractEmailService):
    def send_activation_email(self, user: UserModel):
        pass

    def send_invites_batch(self, users: list[UserModel]):
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
        activation_url = self.shopify_service.get_account_activation_url(user.shopify_id)

        template_model = {"first_name": user.first_name, "shopify_url": activation_url}
        body = {
            "From": FROM_EMAIL,
            "To": user.email,
            "TemplateId": PostmarkTemplates.ACTIVATION,
            "TemplateModel": template_model,
        }
        self._postmark_request("POST", "email/withTemplate", body)

    def send_invites_batch(self, users: list[UserModel]):
        batch = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = (executor.submit(self._invites_batch_prepare_one, user) for user in users)
            for future in as_completed(futures):
                batch.append(future.result())
        self._postmark_request("POST", "email/batchWithTemplates", {"Messages": batch})

    def _invites_batch_prepare_one(self, user: UserModel):
        if not user.account_status:
            shopify_url = self.shopify_service.get_account_activation_url(user.shopify_id)
            button_text = "Activate Account & Get Started"
        else:
            shopify_url = self.shopify_service.get_account_login_url(user.shopify_id)
            button_text = "Get Started"

        template_model = {"first_name": user.first_name, "shopify_url": shopify_url, "button_text": button_text}
        body = {
            "From": FROM_EMAIL,
            "To": user.email,
            "TemplateId": PostmarkTemplates.INVITE,
            "TemplateModel": template_model,
        }
        return body
