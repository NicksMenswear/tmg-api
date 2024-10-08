import json
from typing import Dict, Any

from pydantic import BaseModel


class AuditLogMessage(BaseModel):
    type: str
    payload: Dict[str, Any]
    request: Dict[str, Any]

    def to_string(self) -> str:
        return json.dumps(self.model_dump())

    @classmethod
    def from_string(cls, string: str) -> "AuditLogMessage":
        return cls.parse_raw(string)
