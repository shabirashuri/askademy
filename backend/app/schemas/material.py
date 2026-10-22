import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.item_bank import MaterialStatus


class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    topic_id: uuid.UUID
    uploaded_by: uuid.UUID
    file_name: str
    file_type: str
    file_size_bytes: int
    status: MaterialStatus
    error_message: str | None
    created_at: datetime
