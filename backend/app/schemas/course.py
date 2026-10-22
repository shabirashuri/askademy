import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip(value: str) -> str:
    return value.strip()


class CourseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    teacher_id: uuid.UUID | None = None

    _strip = field_validator("code", "title")(_strip)


class CourseUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("code", "title")
    @classmethod
    def _strip_optional(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    description: str | None
    teacher_id: uuid.UUID
    created_at: datetime
