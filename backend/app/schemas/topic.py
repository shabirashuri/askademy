import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TopicCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    parent_topic_id: uuid.UUID | None = None

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str) -> str:
        return value.strip()


class TopicUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str) -> str:
        return value.strip()


class TopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    parent_topic_id: uuid.UUID | None
    title: str
    position: int


class TopicOrderItem(BaseModel):
    id: uuid.UUID
    position: int = Field(ge=0)


class TopicOrder(BaseModel):
    items: list[TopicOrderItem] = Field(min_length=1)
