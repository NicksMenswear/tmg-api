from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr


class CreateUserModel(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    account_status: bool = True


class UserModel(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    shopify_id: Union[None, str] = None
    account_status: bool = False
    legacy_id: Union[None, str] = None
    phone_number: Union[None, str] = None

    class Config:
        from_attributes = True
        orm_mode = True

    def to_response(self):
        return self.dict(include={"id", "first_name", "last_name", "email"})


class UpdateUserModel(BaseModel):
    first_name: str
    last_name: str
