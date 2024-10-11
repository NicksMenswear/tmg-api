import logging
import uuid
from typing import Dict, Any

from server.database.database_manager import db
from server.database.models import Webhook
from server.models.webhook_model import WebhookModel
from server.services import ServiceError, NotFoundError

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class WebhookService:
    def store_webhook(self, webhook_type: str, payload: Dict[str, Any]) -> WebhookModel:
        try:
            webhook = Webhook(
                type=webhook_type,
                payload=payload,
            )
            db.session.add(webhook)
            db.session.commit()
            db.session.refresh(webhook)

            return WebhookModel.model_validate(webhook)
        except Exception as e:
            raise ServiceError("Failed to store webhook", e)

    def get_webhook_by_id(self, webhook_id: uuid.UUID) -> WebhookModel:
        webhook = Webhook.query.filter(Webhook.id == webhook_id).first()

        if not webhook:
            raise NotFoundError("Webhook not found")

        return WebhookModel.model_validate(webhook)
