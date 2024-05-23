from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class CreateUserModel(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    account_status: bool = False


class UserModel(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    shopify_id: str
    account_status: bool = False
    legacy_id: Optional[str]
    phone_number: Optional[str]

    class Config:
        from_attributes = True
        orm_mode = True

    def to_response(self):
        return self.dict(include={"id", "first_name", "last_name", "email"})


class UpdateUserModel(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
