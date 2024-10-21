import json
from typing import Dict, Any, Optional
from uuid import UUID

from pydantic import BaseModel


class AuditLogMessage(BaseModel):
    id: UUID
    type: str
    payload: Dict[str, Any]
    request: Dict[str, Any]
    diff: Optional[Dict[str, Any]] = None

    def to_string(self) -> str:
        return json.dumps(self.model_dump())

    @classmethod
    def from_string(cls, string: str) -> "AuditLogMessage":
        return cls.model_validate_json(string)
