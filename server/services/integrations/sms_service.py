from base64 import b64encode
import logging
import os
from abc import ABC, abstractmethod

from server.services import ServiceError
from server.controllers.util import http

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_PHONE_NUMBER")

logger = logging.getLogger(__name__)


class AbstractSmsService(ABC):
    @abstractmethod
    def send_tracking(self, phone_number: str, code: str) -> None:
        pass


class FakeSmsService(AbstractSmsService):
    def __init__(self) -> None:
        self.sent_messages = {}

    def send_tracking(self, phone_number: str, code: str) -> None:
        self.sent_messages.get(phone_number, []).append(code)

    def send_order_confirmation(self, phone_number: str, order_id: str) -> None:
        self.sent_messages.get(phone_number, []).append(order_id)


class SmsService(AbstractSmsService):
    def __init__(self) -> None:
        pass

    def send_tracking(self, phone_number: str, tracking_code: str) -> None:
        try:
            message_body = f"The Modern Groom has shipped your order! Tracking code: {tracking_code}"
            self.__send_message(phone_number, message_body)
        except Exception as e:
            logger.exception(e)

    def send_order_confirmation(self, phone_number: str, order_number: str) -> None:
        try:
            message_body = f"The Modern Groom has received your order! Order number: {order_number}"
            self.__send_message(phone_number, message_body)
        except Exception as e:
            logger.exception(e)

    def __send_message(self, phone_number: str, message: str) -> None:
        body = {
            "From": TWILIO_FROM,
            "To": phone_number,
            "Body": message,
        }

        self.__twilio_request("POST", f"Accounts/{TWILIO_ACCOUNT_SID}/Messages.json", body)

    @staticmethod
    def __twilio_request(method, path, json) -> None:
        headers = {"Authorization": f"Basic {TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"}
        credentials = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
        encoded_credentials = b64encode(credentials.encode("utf-8")).decode("utf-8")
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
        }

        response = http(
            method,
            f"https://api.twilio.com/2010-04-01/{path}",
            headers=headers,
            json=json,
        )

        if response.status >= 400:
            raise ServiceError(f"Error sending Twilio SMS: {response.data.decode('utf-8')}")
