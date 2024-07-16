from typing import Any, Dict
from uuid import UUID

from server.models import CoreModel


class WebhookModel(CoreModel):
    id: UUID
    type: str
    payload: Dict[str, Any]

    class Config:
        from_attributes = True

    def to_response(self):
        return self.model_dump()
