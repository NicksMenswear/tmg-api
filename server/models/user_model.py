import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, validator, field_validator


class UserRequestModel(BaseModel):
    first_name: str
    last_name: str

    @field_validator("first_name", "last_name")
    @classmethod
    def name_length_and_characters(cls, v):
        if len(v) < 2 or len(v) > 50:
            raise ValueError("Name must be between 2 and 50 characters long")

        if not re.match(r"^[a-zA-Z\s\-'.]+$", v):
            raise ValueError("Name must contain only alphabetic characters, spaces, dashes, apostrophes, or periods")

        return v


class CreateUserModel(UserRequestModel):
    email: EmailStr
    account_status: bool = True


class UserModel(BaseModel):
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
        return self.dict(include={"id", "first_name", "last_name", "email"})


class UpdateUserModel(UserRequestModel):
    pass
