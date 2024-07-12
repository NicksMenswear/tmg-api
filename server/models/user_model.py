import re
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, field_validator

from server.models import CoreModel


class UserRequestModel(CoreModel):
    first_name: str
    last_name: str
    account_status: Optional[bool] = False
    shopify_id: Optional[str] = None
    phone_number: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def name_length_and_characters(cls, v):
        if len(v) < 2 or len(v) > 50:
            raise ValueError("Name must be between 2 and 50 characters long")

        if not re.match(r"^[a-zA-Z0-9\s\-'.]+$", v):
            raise ValueError("Name must contain only alphabetic characters, spaces, dashes, apostrophes, or periods")

        return v


class CreateUserModel(UserRequestModel):
    email: EmailStr


class UserModel(CoreModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    shopify_id: Optional[str] = None
    account_status: bool = False
    legacy_id: Optional[str] = None
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True

    def to_response(self):
        return self.model_dump(include={"id", "first_name", "last_name", "email"})


class UpdateUserModel(UserRequestModel):
    pass
