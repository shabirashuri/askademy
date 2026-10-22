import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import DbSession, require_roles
from app.models import CourseEnrollment, User
from app.models.user import UserRole
from app.schemas.enrollment import EnrollmentCreate, EnrollmentRead
from app.services import enrollment_service

router = APIRouter(prefix="/courses/{course_id}/enrollments", tags=["enrollments"])

StaffUser = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER))]


@router.get("", response_model=list[EnrollmentRead], summary="List enrolled students")
def list_enrollments(
    course_id: uuid.UUID, db: DbSession, user: StaffUser
) -> list[CourseEnrollment]:
    return enrollment_service.list_enrollments(db, user, course_id)


@router.post(
    "", response_model=EnrollmentRead, status_code=201, summary="Enroll a student in a course"
)
def enroll_student(
    course_id: uuid.UUID, payload: EnrollmentCreate, db: DbSession, user: StaffUser
) -> CourseEnrollment:
    return enrollment_service.enroll_student(db, user, course_id, payload.student_id)


@router.delete("/{student_id}", status_code=204, summary="Remove a student from a course")
def unenroll_student(
    course_id: uuid.UUID, student_id: uuid.UUID, db: DbSession, user: StaffUser
) -> Response:
    enrollment_service.unenroll_student(db, user, course_id, student_id)
    return Response(status_code=204)
