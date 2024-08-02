import json
import os
from abc import ABC, abstractmethod
from urllib.parse import urlencode
import logging

from server.controllers.util import http
from server.services import ServiceError, DuplicateError
from server.services.integrations.activecampaign_fields import field_resolver

logger = logging.getLogger(__name__)


STAGE = os.getenv("STAGE")
ACTIVECAMPAIGN_API_URL = os.getenv("ACTIVECAMPAIGN_API_URL")
ACTIVECAMPAIGN_API_KEY = os.getenv("ACTIVECAMPAIGN_API_KEY")


class AbstractActiveCampaignService(ABC):
    @abstractmethod
    def sync_contact(
        self, email, first_name=None, last_name=None, phone=None, fields={}, events=[], suppress_exceptions=True
    ):
        pass

    @abstractmethod
    def track_event(self, email, event, suppress_exceptions=True):
        pass


class FakeActiveCampaignService(AbstractActiveCampaignService):
    def sync_contact(
        self, email, first_name=None, last_name=None, phone=None, fields={}, events=[], suppress_exceptions=True
    ):
        pass

    def track_event(self, email, event, suppress_exceptions=True):
        pass


class ActiveCampaignService(AbstractActiveCampaignService):
    def sync_contact(
        self, email, first_name=None, last_name=None, phone=None, fields={}, events=[], suppress_exceptions=True
    ):
        try:
            body = {
                "contact": {
                    "email": email,
                },
            }
            if first_name:
                body["contact"]["firstName"] = first_name
            if last_name:
                body["contact"]["lastName"] = last_name
            if phone:
                body["contact"]["phone"] = last_name
            if fields:
                body["contact"]["fieldValues"] = field_resolver(fields)

            self._activecampaign_request("POST", "contact/sync", body)

            for event in events:
                self.track_event(email, event)
        except Exception as e:
            if suppress_exceptions:
                logger.exception(e)
            else:
                raise

    def track_event(self, email, event, suppress_exceptions=True):
        try:
            url = "https://trackcmp.net/event"
            payload = {
                # These IDs are shared on FE so safe to hardcode
                "actid": "1000679488",
                "key": "d19165c01ccb298a7b080576932716047ce11d5c",
                "event": event,
                "visit": json.dumps({"email": email}),
            }
            headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}

            response = http("POST", url, headers=headers, body=urlencode(payload))
            if response.status >= 400:
                raise ServiceError(f"Error using ActiveCampaign Tracking: {response.data.decode('utf-8')}")
        except Exception as e:
            if suppress_exceptions:
                logger.exception(e)
            else:
                raise

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
        if response.status >= 400:
            raise ServiceError(f"Error using ActiveCampaign: {response.data.decode('utf-8')}")
