import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.errors import Conflict, NotFound, ValidationFailed
from app.models import CourseEnrollment, User
from app.models.user import UserRole
from app.services import course_service


def list_enrollments(db: Session, user: User, course_id: uuid.UUID) -> list[CourseEnrollment]:
    course = course_service.get_course(db, user, course_id, write=True)
    return list(
        db.scalars(
            select(CourseEnrollment)
            .options(joinedload(CourseEnrollment.student))
            .join(User, User.id == CourseEnrollment.student_id)
            .where(CourseEnrollment.course_id == course.id)
            .order_by(User.full_name)
        )
    )


def enroll_student(
    db: Session, user: User, course_id: uuid.UUID, student_id: uuid.UUID
) -> CourseEnrollment:
    course = course_service.get_course(db, user, course_id, write=True)
    student = db.get(User, student_id)
    if student is None or student.role != UserRole.STUDENT or not student.is_active:
        raise ValidationFailed("The selected user is not an active student.")
    enrollment = CourseEnrollment(course_id=course.id, student_id=student.id)
    db.add(enrollment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict("This student is already enrolled in the course.") from None
    db.refresh(enrollment)
    return enrollment


def unenroll_student(db: Session, user: User, course_id: uuid.UUID, student_id: uuid.UUID) -> None:
    course = course_service.get_course(db, user, course_id, write=True)
    enrollment = db.scalar(
        select(CourseEnrollment).where(
            CourseEnrollment.course_id == course.id, CourseEnrollment.student_id == student_id
        )
    )
    if enrollment is None:
        raise NotFound("This student is not enrolled in the course.")
    db.delete(enrollment)
    db.commit()
