import uuid
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Response, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import DbSession, require_roles
from app.models import Material, User
from app.models.user import UserRole
from app.schemas.material import MaterialRead
from app.services import material_service
from app.services.storage import StorageBackend, get_storage

router = APIRouter(tags=["materials"])

StaffUser = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER))]
Storage = Annotated[StorageBackend, Depends(get_storage)]


@router.post(
    "/courses/{course_id}/topics/{topic_id}/materials",
    response_model=MaterialRead,
    status_code=201,
    summary="Upload a PDF, PPTX or DOCX file to a topic",
)
def upload_material(
    course_id: uuid.UUID,
    topic_id: uuid.UUID,
    db: DbSession,
    storage: Storage,
    user: StaffUser,
    file: Annotated[UploadFile, File()],
) -> Material:
    return material_service.upload_material(
        db, storage, user, course_id, topic_id, file.filename, file.file
    )


@router.get(
    "/courses/{course_id}/materials",
    response_model=list[MaterialRead],
    summary="List a course's materials",
)
def list_materials(
    course_id: uuid.UUID, db: DbSession, user: StaffUser, topic_id: uuid.UUID | None = None
) -> list[Material]:
    return material_service.list_materials(db, user, course_id, topic_id)


@router.get("/materials/{material_id}/download", summary="Download a material file")
def download_material(
    material_id: uuid.UUID, db: DbSession, storage: Storage, user: StaffUser
) -> StreamingResponse:
    material = material_service.get_material(db, user, material_id)

    def stream():
        with storage.open(material.storage_path) as handle:
            while chunk := handle.read(material_service.CHUNK_SIZE):
                yield chunk

    return StreamingResponse(
        stream(),
        media_type=material_service.MEDIA_TYPES[material.file_type],
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(material.file_name)}",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete("/materials/{material_id}", status_code=204, summary="Delete a material (soft)")
def delete_material(material_id: uuid.UUID, db: DbSession, user: StaffUser) -> Response:
    material_service.delete_material(db, user, material_id)
    return Response(status_code=204)
