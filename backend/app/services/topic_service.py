import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import Conflict, NotFound, ValidationFailed
from app.models import Material, Topic, User
from app.schemas.topic import TopicCreate, TopicOrder, TopicUpdate
from app.services import course_service

DUPLICATE_MESSAGE = "A topic with this title already exists here."


def list_topics(db: Session, user: User, course_id: uuid.UUID) -> list[Topic]:
    course_service.get_course(db, user, course_id)
    return list(
        db.scalars(
            select(Topic)
            .where(Topic.course_id == course_id, Topic.deleted_at.is_(None))
            .order_by(Topic.position, Topic.title)
        )
    )


def _get_topic(db: Session, topic_id: uuid.UUID) -> Topic:
    topic = db.scalar(select(Topic).where(Topic.id == topic_id, Topic.deleted_at.is_(None)))
    if topic is None:
        raise NotFound("Topic not found.")
    return topic


def get_topic(db: Session, user: User, topic_id: uuid.UUID, *, write: bool = False) -> Topic:
    topic = _get_topic(db, topic_id)
    course_service.get_course(db, user, topic.course_id, write=write)
    return topic


def _ensure_title_free(
    db: Session,
    course_id: uuid.UUID,
    parent_id: uuid.UUID | None,
    title: str,
    exclude_id: uuid.UUID | None = None,
) -> None:
    stmt = select(Topic.id).where(
        Topic.course_id == course_id,
        Topic.deleted_at.is_(None),
        func.lower(Topic.title) == title.lower(),
        Topic.parent_topic_id.is_(None)
        if parent_id is None
        else Topic.parent_topic_id == parent_id,
    )
    if exclude_id is not None:
        stmt = stmt.where(Topic.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise Conflict(DUPLICATE_MESSAGE)


def create_topic(db: Session, user: User, course_id: uuid.UUID, data: TopicCreate) -> Topic:
    course = course_service.get_course(db, user, course_id, write=True)
    if data.parent_topic_id is not None:
        parent = _get_topic(db, data.parent_topic_id)
        if parent.course_id != course.id:
            raise ValidationFailed("The parent topic belongs to a different course.")
    _ensure_title_free(db, course.id, data.parent_topic_id, data.title)
    next_position = db.scalar(
        select(func.coalesce(func.max(Topic.position) + 1, 0)).where(
            Topic.course_id == course.id,
            Topic.deleted_at.is_(None),
            Topic.parent_topic_id.is_(None)
            if data.parent_topic_id is None
            else Topic.parent_topic_id == data.parent_topic_id,
        )
    )
    topic = Topic(
        course_id=course.id,
        parent_topic_id=data.parent_topic_id,
        title=data.title,
        position=next_position,
    )
    db.add(topic)
    _commit(db)
    db.refresh(topic)
    return topic


def update_topic(db: Session, user: User, topic_id: uuid.UUID, data: TopicUpdate) -> Topic:
    topic = get_topic(db, user, topic_id, write=True)
    _ensure_title_free(db, topic.course_id, topic.parent_topic_id, data.title, topic.id)
    topic.title = data.title
    _commit(db)
    db.refresh(topic)
    return topic


def delete_topic(db: Session, user: User, topic_id: uuid.UUID) -> None:
    topic = get_topic(db, user, topic_id, write=True)
    ids = {topic.id}
    frontier = [topic.id]
    while frontier:
        children = list(
            db.scalars(
                select(Topic.id).where(
                    Topic.parent_topic_id.in_(frontier), Topic.deleted_at.is_(None)
                )
            )
        )
        frontier = [c for c in children if c not in ids]
        ids.update(frontier)
    now = datetime.now(UTC)
    db.execute(
        update(Material)
        .where(Material.topic_id.in_(ids), Material.deleted_at.is_(None))
        .values(deleted_at=now)
    )
    db.execute(update(Topic).where(Topic.id.in_(ids)).values(deleted_at=now))
    db.commit()


def reorder_topics(db: Session, user: User, course_id: uuid.UUID, order: TopicOrder) -> list[Topic]:
    course_service.get_course(db, user, course_id, write=True)
    topics = {
        t.id: t
        for t in db.scalars(
            select(Topic).where(Topic.course_id == course_id, Topic.deleted_at.is_(None))
        )
    }
    for item in order.items:
        if item.id not in topics:
            raise ValidationFailed("One or more topics do not belong to this course.")
    for item in order.items:
        topics[item.id].position = item.position
    db.commit()
    return list_topics(db, user, course_id)


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict(DUPLICATE_MESSAGE) from None
