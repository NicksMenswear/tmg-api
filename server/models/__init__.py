from pydantic import BaseModel, field_validator


class CoreModel(BaseModel):
    @field_validator("*")
    def strip_whitespace(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value
