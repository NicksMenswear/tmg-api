from typing import Optional
from uuid import UUID

from pydantic import EmailStr

from server.models import CoreModel


class UserRequestModel(CoreModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: EmailStr
    account_status: Optional[bool] = False
    shopify_id: Optional[str] = None
    phone_number: Optional[str] = None


class CreateUserModel(UserRequestModel):
    pass


class UserModel(CoreModel):
    id: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    email: EmailStr
    shopify_id: Optional[str] = None
    account_status: bool = False
    legacy_id: Optional[str] = None
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True

    def to_response(self):
        return self.model_dump(
            include={"id", "first_name", "last_name", "email", "phone_number", "account_status", "shopify_id"}
        )


class UpdateUserModel(UserRequestModel):
    pass
