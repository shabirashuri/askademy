import pytest

from app.models.user import UserRole

API = "/api/v1"


@pytest.fixture
def teacher(make_user):
    return make_user(UserRole.TEACHER)


@pytest.fixture
def student(make_user):
    return make_user(UserRole.STUDENT, full_name="Sam Student")


@pytest.fixture
def course(client, teacher, auth_headers):
    r = client.post(
        f"{API}/courses",
        json={"code": "CS301", "title": "Database Systems"},
        headers=auth_headers(teacher),
    )
    return r.json()


def enroll(client, headers, course_id, student_id):
    return client.post(
        f"{API}/courses/{course_id}/enrollments",
        json={"student_id": str(student_id)},
        headers=headers,
    )


def test_teacher_enrolls_lists_and_removes_student(client, teacher, student, course, auth_headers):
    h = auth_headers(teacher)
    r = enroll(client, h, course["id"], student.id)
    assert r.status_code == 201
    assert r.json()["student"]["email"] == student.email
    assert "password_hash" not in r.json()["student"]

    listed = client.get(f"{API}/courses/{course['id']}/enrollments", headers=h).json()
    assert [e["student_id"] for e in listed] == [str(student.id)]

    r = client.delete(f"{API}/courses/{course['id']}/enrollments/{student.id}", headers=h)
    assert r.status_code == 204
    assert client.get(f"{API}/courses/{course['id']}/enrollments", headers=h).json() == []


def test_enrolled_student_sees_course_and_loses_it_after_removal(
    client, teacher, student, course, auth_headers
):
    enroll(client, auth_headers(teacher), course["id"], student.id)
    sh = auth_headers(student)
    assert [c["id"] for c in client.get(f"{API}/courses", headers=sh).json()] == [course["id"]]
    client.delete(
        f"{API}/courses/{course['id']}/enrollments/{student.id}", headers=auth_headers(teacher)
    )
    assert client.get(f"{API}/courses", headers=sh).json() == []


def test_duplicate_enrollment_conflicts(client, teacher, student, course, auth_headers):
    h = auth_headers(teacher)
    assert enroll(client, h, course["id"], student.id).status_code == 201
    assert enroll(client, h, course["id"], student.id).status_code == 409


def test_only_active_students_can_be_enrolled(client, teacher, make_user, course, auth_headers):
    h = auth_headers(teacher)
    for other in (make_user(UserRole.TEACHER), make_user(UserRole.ADMIN)):
        assert enroll(client, h, course["id"], other.id).status_code == 422
    inactive = make_user(UserRole.STUDENT, is_active=False)
    assert enroll(client, h, course["id"], inactive.id).status_code == 422
    import uuid

    assert enroll(client, h, course["id"], uuid.uuid4()).status_code == 422


def test_removing_unknown_enrollment_is_404(client, teacher, student, course, auth_headers):
    r = client.delete(
        f"{API}/courses/{course['id']}/enrollments/{student.id}", headers=auth_headers(teacher)
    )
    assert r.status_code == 404


def test_other_teacher_cannot_manage_enrollments(client, make_user, student, course, auth_headers):
    foreign = auth_headers(make_user(UserRole.TEACHER))
    assert (
        client.get(f"{API}/courses/{course['id']}/enrollments", headers=foreign).status_code == 404
    )
    assert enroll(client, foreign, course["id"], student.id).status_code == 404
    assert (
        client.delete(
            f"{API}/courses/{course['id']}/enrollments/{student.id}", headers=foreign
        ).status_code
        == 404
    )


def test_student_cannot_manage_or_list_enrollments(
    client, teacher, student, make_user, course, auth_headers
):
    other = make_user(UserRole.STUDENT)
    enroll(client, auth_headers(teacher), course["id"], student.id)
    sh = auth_headers(student)
    assert client.get(f"{API}/courses/{course['id']}/enrollments", headers=sh).status_code == 403
    assert enroll(client, sh, course["id"], other.id).status_code == 403


def test_admin_can_manage_any_course_enrollments(client, student, make_user, course, auth_headers):
    h = auth_headers(make_user(UserRole.ADMIN))
    assert enroll(client, h, course["id"], student.id).status_code == 201
    assert len(client.get(f"{API}/courses/{course['id']}/enrollments", headers=h).json()) == 1


def test_admin_cannot_deactivate_self(client, make_user, auth_headers):
    admin = make_user(UserRole.ADMIN)
    r = client.patch(
        f"{API}/users/{admin.id}", json={"is_active": False}, headers=auth_headers(admin)
    )
    assert r.status_code == 422
