import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import Conflict, Forbidden, NotFound, ValidationFailed
from app.models import Course, CourseEnrollment, Material, Topic, User
from app.models.user import UserRole
from app.schemas.course import CourseCreate, CourseUpdate


def _visible_courses_stmt(user: User):
    stmt = select(Course).where(Course.deleted_at.is_(None))
    if user.role == UserRole.TEACHER:
        stmt = stmt.where(Course.teacher_id == user.id)
    elif user.role == UserRole.STUDENT:
        stmt = stmt.join(CourseEnrollment, CourseEnrollment.course_id == Course.id).where(
            CourseEnrollment.student_id == user.id
        )
    return stmt


def list_courses(db: Session, user: User) -> list[Course]:
    return list(db.scalars(_visible_courses_stmt(user).order_by(Course.code)))


def get_course(db: Session, user: User, course_id: uuid.UUID, *, write: bool = False) -> Course:
    """Return a course the user may see; hide courses they cannot see behind a 404."""
    course = db.scalar(_visible_courses_stmt(user).where(Course.id == course_id))
    if course is None:
        raise NotFound("Course not found.")
    if write and user.role == UserRole.STUDENT:
        raise Forbidden("You do not have permission to modify this course.")
    return course


def create_course(db: Session, user: User, data: CourseCreate) -> Course:
    if user.role == UserRole.ADMIN:
        if data.teacher_id is None:
            raise ValidationFailed("An administrator must choose the teacher who owns the course.")
        teacher = db.get(User, data.teacher_id)
        if teacher is None or teacher.role != UserRole.TEACHER or not teacher.is_active:
            raise ValidationFailed("The selected teacher does not exist.")
        teacher_id = teacher.id
    else:
        teacher_id = user.id
    course = Course(
        code=data.code, title=data.title, description=data.description, teacher_id=teacher_id
    )
    db.add(course)
    _commit_or_conflict(db, "A course with this code already exists.")
    db.refresh(course)
    return course


def update_course(db: Session, user: User, course_id: uuid.UUID, data: CourseUpdate) -> Course:
    course = get_course(db, user, course_id, write=True)
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is None and field != "description":
            continue
        setattr(course, field, value)
    _commit_or_conflict(db, "A course with this code already exists.")
    db.refresh(course)
    return course


def delete_course(db: Session, user: User, course_id: uuid.UUID) -> None:
    course = get_course(db, user, course_id, write=True)
    now = datetime.now(UTC)
    db.execute(
        update(Material)
        .where(Material.course_id == course.id, Material.deleted_at.is_(None))
        .values(deleted_at=now)
    )
    db.execute(
        update(Topic)
        .where(Topic.course_id == course.id, Topic.deleted_at.is_(None))
        .values(deleted_at=now)
    )
    course.deleted_at = now
    db.commit()


def _commit_or_conflict(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict(message) from None
