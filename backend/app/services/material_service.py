import hashlib
import re
import uuid
import zipfile
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import Conflict, NotFound, ValidationFailed
from app.models import Material, User
from app.models.item_bank import MaterialStatus
from app.services import course_service, topic_service
from app.services.storage import StorageBackend

ALLOWED_TYPES = {"pdf", "pptx", "docx"}
CHUNK_SIZE = 64 * 1024
ZIP_MARKERS = {"docx": "word/document.xml", "pptx": "ppt/presentation.xml"}
MEDIA_TYPES = {
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def sanitize_file_name(name: str | None) -> str:
    base = (name or "").replace("\\", "/").split("/")[-1]
    base = re.sub(r"[\x00-\x1f\x7f]", "", base).strip()
    return base[:255]


def _file_type(file_name: str) -> str:
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if ext not in ALLOWED_TYPES:
        raise ValidationFailed("Only PDF, PPTX and DOCX files can be uploaded.")
    return ext


class _Upload:
    """Wraps the incoming stream: enforces the size limit and hashes while it is stored."""

    def __init__(self, source: BinaryIO, file_type: str, max_bytes: int) -> None:
        self.source = source
        self.file_type = file_type
        self.max_bytes = max_bytes
        self.size = 0
        self.digest = hashlib.sha256()

    def chunks(self) -> Iterator[bytes]:
        first = True
        while chunk := self.source.read(CHUNK_SIZE):
            if first:
                first = False
                self._check_signature(chunk)
            self.size += len(chunk)
            if self.size > self.max_bytes:
                raise ValidationFailed(
                    f"The file is larger than the {settings.max_upload_mb} MB limit."
                )
            self.digest.update(chunk)
            yield chunk
        if first:
            raise ValidationFailed("The file is empty.")

    def _check_signature(self, head: bytes) -> None:
        expected = b"%PDF-" if self.file_type == "pdf" else b"PK\x03\x04"
        if not head.startswith(expected):
            raise ValidationFailed("The file content does not match its extension.")


def _validate_container(storage: StorageBackend, key: str, file_type: str) -> None:
    marker = ZIP_MARKERS.get(file_type)
    if marker is None:
        return
    with storage.open(key) as handle:
        try:
            with zipfile.ZipFile(handle) as archive:
                names = set(archive.namelist())
        except zipfile.BadZipFile:
            raise ValidationFailed("The file is corrupted or not a valid document.") from None
    if "[Content_Types].xml" not in names or marker not in names:
        raise ValidationFailed("The file content does not match its extension.")


def upload_material(
    db: Session,
    storage: StorageBackend,
    user: User,
    course_id: uuid.UUID,
    topic_id: uuid.UUID,
    file_name: str | None,
    stream: BinaryIO,
) -> Material:
    course = course_service.get_course(db, user, course_id, write=True)
    topic = topic_service.get_topic(db, user, topic_id, write=True)
    if topic.course_id != course.id:
        raise NotFound("Topic not found.")

    clean_name = sanitize_file_name(file_name)
    file_type = _file_type(clean_name)
    upload = _Upload(stream, file_type, settings.max_upload_mb * 1024 * 1024)
    key = f"courses/{course.id}/{uuid.uuid4().hex}.{file_type}"

    storage.save(key, upload.chunks())
    try:
        _validate_container(storage, key, file_type)
        content_hash = upload.digest.hexdigest()
        existing = db.scalar(
            select(Material.id).where(
                Material.course_id == course.id,
                Material.content_hash == content_hash,
                Material.deleted_at.is_(None),
            )
        )
        if existing is not None:
            raise Conflict(
                "This file has already been uploaded to the course.",
                existing_material_id=str(existing),
            )
        material = Material(
            course_id=course.id,
            topic_id=topic.id,
            uploaded_by=user.id,
            file_name=clean_name,
            file_type=file_type,
            storage_path=key,
            file_size_bytes=upload.size,
            content_hash=content_hash,
            status=MaterialStatus.UPLOADED,
        )
        db.add(material)
        db.commit()
    except BaseException:
        db.rollback()
        storage.delete(key)
        raise
    db.refresh(material)
    return material


def list_materials(
    db: Session, user: User, course_id: uuid.UUID, topic_id: uuid.UUID | None = None
) -> list[Material]:
    course = course_service.get_course(db, user, course_id, write=True)
    stmt = select(Material).where(Material.course_id == course.id, Material.deleted_at.is_(None))
    if topic_id is not None:
        stmt = stmt.where(Material.topic_id == topic_id)
    return list(db.scalars(stmt.order_by(Material.created_at.desc())))


def get_material(db: Session, user: User, material_id: uuid.UUID) -> Material:
    material = db.scalar(
        select(Material).where(Material.id == material_id, Material.deleted_at.is_(None))
    )
    if material is None:
        raise NotFound("Material not found.")
    course_service.get_course(db, user, material.course_id, write=True)
    return material


def delete_material(db: Session, user: User, material_id: uuid.UUID) -> None:
    material = get_material(db, user, material_id)
    material.deleted_at = datetime.now(UTC)
    db.commit()
