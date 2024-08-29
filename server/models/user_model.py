import re
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, field_validator

from server.models import CoreModel


class UserRequestModel(CoreModel):
    first_name: str
    last_name: str
    email: EmailStr
    account_status: Optional[bool] = False
    shopify_id: Optional[str] = None
    phone_number: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def name_length_and_characters(cls, v):
        if len(v) < 1 or len(v) > 63:
            raise ValueError("Name must be between 1 and 63 characters long")

        if not re.match(r"^[\w\s\-'.,À-ÖØ-öø-ÿĀ-ſ&’]+$", v, re.UNICODE):
            raise ValueError(
                "Name must only contain alphabetic characters, spaces, dashes, apostrophes, periods or commas"
            )

        return v


class CreateUserModel(UserRequestModel):
    pass


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
