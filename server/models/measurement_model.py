from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime

from pydantic import EmailStr

from server.database.models import Measurement
from server.models import CoreModel


class CreateMeasurementsRequestModel(CoreModel):
    user_id: UUID
    email: Optional[EmailStr]
    data: dict


class MeasurementModel(CoreModel):
    id: UUID
    user_id: Optional[UUID]
    email: Optional[EmailStr]
    data: Dict[str, Any]
    gender_type: str
    gender: str
    weight: int
    height: int
    age: str
    chest_shape: str
    stomach_shape: str
    hip_shape: str
    shoe_size: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def model_validate(cls, measurement: Measurement) -> "MeasurementModel":
        return cls(
            id=measurement.id,
            user_id=measurement.user_id,
            data=measurement.data,
            gender_type=measurement.data.get("genderType"),
            gender=measurement.data.get("gender"),
            weight=measurement.data.get("weight"),
            height=measurement.data.get("height"),
            age=measurement.data.get("age"),
            chest_shape=measurement.data.get("chestShape"),
            stomach_shape=measurement.data.get("stomachShape"),
            hip_shape=measurement.data.get("hipShape"),
            shoe_size=measurement.data.get("shoeSize"),
            created_at=measurement.created_at,
            updated_at=measurement.updated_at,
        )

    def to_response(self):
        return self.model_dump()
