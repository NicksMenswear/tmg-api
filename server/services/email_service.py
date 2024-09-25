import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict
from urllib.parse import urlencode

from server.controllers.util import http
from server.models.event_model import EventModel, EventTypeModel
from server.models.user_model import UserModel
from server.services import ServiceError
from server.services.integrations.shopify_service import AbstractShopifyService

POSTMARK_API_URL = os.getenv("POSTMARK_API_URL")
POSTMARK_API_KEY = os.getenv("POSTMARK_API_KEY")
FROM_EMAIL = "info@themoderngroom.com"


class PostmarkTemplates:
    ACTIVATION = 36199819
    INVITE_DEFAULT = 36555557
    INVITE_WEDDING = 36201238


class AbstractEmailService(ABC):
    @abstractmethod
    def send_activation_email(self, user: UserModel) -> None:
        pass

    @abstractmethod
    def send_invites_batch(self, event: EventModel, users: list[UserModel]) -> None:
        pass


class FakeEmailService(AbstractEmailService):
    def __init__(self):
        self.__sent_invites = {}

    def send_activation_email(self, user: UserModel) -> None:
        pass

    def send_invites_batch(self, event: EventModel, users: list[UserModel]) -> None:
        self.__sent_invites[event.id] = self.__sent_invites.get(event.id, set())

        for user in users:
            self.__sent_invites[event.id].add(user.id)


class EmailService(AbstractEmailService):
    def __init__(self, shopify_service: AbstractShopifyService) -> None:
        self.shopify_service = shopify_service

    @staticmethod
    def __postmark_request(method, path, json) -> None:
        headers = {"X-Postmark-Server-Token": POSTMARK_API_KEY}

        response = http(
            method,
            f"{POSTMARK_API_URL}/{path}",
            headers=headers,
            json=json,
        )

        if response.status >= 400:
            raise ServiceError(f"Error sending email: {response.data.decode('utf-8')}")

    def send_activation_email(self, user: UserModel) -> None:
        activation_url = self._get_account_activation_url(user)

        template_model = {"first_name": user.first_name, "shopify_url": activation_url}
        body = {
            "From": FROM_EMAIL,
            "To": user.email,
            "TemplateId": PostmarkTemplates.ACTIVATION,
            "TemplateModel": template_model,
        }

        self.__postmark_request("POST", "email/withTemplate", body)

    def send_invites_batch(self, event: EventModel, users: list[UserModel]) -> None:
        batch = []

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = (executor.submit(self._invites_batch_prepare_one, user, event) for user in users)
            for future in as_completed(futures):
                batch.append(future.result())

        self.__postmark_request("POST", "email/batchWithTemplates", {"Messages": batch})

    def _invites_batch_prepare_one(self, user: UserModel, event: EventModel) -> Dict[str, Any]:
        if not user.account_status:
            shopify_url = self._get_account_activation_url(user)
            button_text = "Activate Account & Get Started"
        else:
            shopify_url = self.shopify_service.get_account_login_url(user.shopify_id)
            button_text = "Get Started"

        template = PostmarkTemplates.INVITE_DEFAULT

        if event.type == EventTypeModel.WEDDING:
            template = PostmarkTemplates.INVITE_WEDDING

        template_model = {
            "first_name": user.first_name,
            "event_name": event.name,
            "shopify_url": shopify_url,
            "button_text": button_text,
        }
        body = {
            "From": FROM_EMAIL,
            "To": user.email,
            "TemplateId": template,
            "TemplateModel": template_model,
        }

        return body

    def _get_account_activation_url(self, user: UserModel) -> str:
        activation_url = self.shopify_service.get_account_activation_url(user.shopify_id)

        url_params = urlencode(
            {"id": user.id, "email": user.email, "first_name": user.first_name, "last_name": user.last_name}
        )

        return f"{activation_url}?{url_params}"
