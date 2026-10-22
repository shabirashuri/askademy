import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import Course, Topic, User
from app.models.user import UserRole
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.schemas.topic import TopicCreate, TopicOrder, TopicRead, TopicUpdate
from app.services import course_service, topic_service

router = APIRouter(tags=["courses"])

StaffUser = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER))]


@router.get("/courses", response_model=list[CourseRead], summary="List courses visible to me")
def list_courses(db: DbSession, user: CurrentUser) -> list[Course]:
    return course_service.list_courses(db, user)


@router.post("/courses", response_model=CourseRead, status_code=201, summary="Create a course")
def create_course(payload: CourseCreate, db: DbSession, user: StaffUser) -> Course:
    return course_service.create_course(db, user, payload)


@router.get("/courses/{course_id}", response_model=CourseRead, summary="Get a course")
def get_course(course_id: uuid.UUID, db: DbSession, user: CurrentUser) -> Course:
    return course_service.get_course(db, user, course_id)


@router.patch("/courses/{course_id}", response_model=CourseRead, summary="Update a course")
def update_course(
    course_id: uuid.UUID, payload: CourseUpdate, db: DbSession, user: StaffUser
) -> Course:
    return course_service.update_course(db, user, course_id, payload)


@router.delete("/courses/{course_id}", status_code=204, summary="Delete a course (soft)")
def delete_course(course_id: uuid.UUID, db: DbSession, user: StaffUser) -> Response:
    course_service.delete_course(db, user, course_id)
    return Response(status_code=204)


@router.get(
    "/courses/{course_id}/topics", response_model=list[TopicRead], summary="List a course's topics"
)
def list_topics(course_id: uuid.UUID, db: DbSession, user: CurrentUser) -> list[Topic]:
    return topic_service.list_topics(db, user, course_id)


@router.post(
    "/courses/{course_id}/topics",
    response_model=TopicRead,
    status_code=201,
    summary="Create a topic or sub-topic",
)
def create_topic(
    course_id: uuid.UUID, payload: TopicCreate, db: DbSession, user: StaffUser
) -> Topic:
    return topic_service.create_topic(db, user, course_id, payload)


@router.put(
    "/courses/{course_id}/topics/order",
    response_model=list[TopicRead],
    summary="Reorder topics",
)
def reorder_topics(
    course_id: uuid.UUID, payload: TopicOrder, db: DbSession, user: StaffUser
) -> list[Topic]:
    return topic_service.reorder_topics(db, user, course_id, payload)


@router.patch("/topics/{topic_id}", response_model=TopicRead, summary="Rename a topic")
def update_topic(
    topic_id: uuid.UUID, payload: TopicUpdate, db: DbSession, user: StaffUser
) -> Topic:
    return topic_service.update_topic(db, user, topic_id, payload)


@router.delete("/topics/{topic_id}", status_code=204, summary="Delete a topic (soft)")
def delete_topic(topic_id: uuid.UUID, db: DbSession, user: StaffUser) -> Response:
    topic_service.delete_topic(db, user, topic_id)
    return Response(status_code=204)
