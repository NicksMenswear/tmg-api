from typing import Any, Dict
from uuid import UUID

from server.database.models import Measurement
from server.models import CoreModel


class CreateMeasurementsRequestModel(CoreModel):
    user_id: UUID
    data: dict


class MeasurementModel(CoreModel):
    id: UUID
    user_id: UUID
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

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, measurement: Measurement) -> "MeasurementModel":
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
        )
