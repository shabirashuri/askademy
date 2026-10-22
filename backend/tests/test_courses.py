import pytest

from app.models import Course, CourseEnrollment, Material, Topic
from app.models.item_bank import MaterialStatus
from app.models.user import UserRole

API = "/api/v1"


@pytest.fixture
def teacher(make_user):
    return make_user(UserRole.TEACHER)


@pytest.fixture
def other_teacher(make_user):
    return make_user(UserRole.TEACHER)


@pytest.fixture
def student(make_user):
    return make_user(UserRole.STUDENT)


@pytest.fixture
def admin(make_user):
    return make_user(UserRole.ADMIN)


def create_course(client, headers, code="CS301", title="Database Systems", **extra):
    r = client.post(f"{API}/courses", json={"code": code, "title": title, **extra}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def create_topic(client, headers, course_id, title="SQL Joins", **extra):
    r = client.post(
        f"{API}/courses/{course_id}/topics", json={"title": title, **extra}, headers=headers
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---- courses ----


def test_teacher_creates_course_owned_by_self(client, teacher, auth_headers):
    course = create_course(client, auth_headers(teacher), description="Intro")
    assert course["teacher_id"] == str(teacher.id)
    assert course["description"] == "Intro"


def test_course_input_is_trimmed_and_validated(client, teacher, auth_headers):
    course = create_course(client, auth_headers(teacher), code="  CS1  ", title="  T  ")
    assert (course["code"], course["title"]) == ("CS1", "T")
    r = client.post(
        f"{API}/courses", json={"code": "", "title": "x"}, headers=auth_headers(teacher)
    )
    assert r.status_code == 422


def test_duplicate_course_code_conflicts(client, teacher, other_teacher, auth_headers):
    create_course(client, auth_headers(teacher), code="DUP")
    r = client.post(
        f"{API}/courses",
        json={"code": "DUP", "title": "Other"},
        headers=auth_headers(other_teacher),
    )
    assert r.status_code == 409


def test_student_cannot_create_course(client, student, auth_headers):
    r = client.post(
        f"{API}/courses", json={"code": "X", "title": "X"}, headers=auth_headers(student)
    )
    assert r.status_code == 403


def test_admin_must_choose_teacher(client, admin, teacher, student, auth_headers):
    h = auth_headers(admin)
    r = client.post(f"{API}/courses", json={"code": "A1", "title": "A"}, headers=h)
    assert r.status_code == 422
    r = client.post(
        f"{API}/courses",
        json={"code": "A1", "title": "A", "teacher_id": str(student.id)},
        headers=h,
    )
    assert r.status_code == 422
    r = client.post(
        f"{API}/courses",
        json={"code": "A1", "title": "A", "teacher_id": str(teacher.id)},
        headers=h,
    )
    assert r.status_code == 201 and r.json()["teacher_id"] == str(teacher.id)


def test_teachers_only_see_own_courses(client, teacher, other_teacher, admin, auth_headers):
    mine = create_course(client, auth_headers(teacher), code="M1")
    theirs = create_course(client, auth_headers(other_teacher), code="T1")

    ids = {c["id"] for c in client.get(f"{API}/courses", headers=auth_headers(teacher)).json()}
    assert ids == {mine["id"]}
    assert (
        client.get(f"{API}/courses/{theirs['id']}", headers=auth_headers(teacher)).status_code
        == 404
    )
    r = client.patch(
        f"{API}/courses/{theirs['id']}", json={"title": "hax"}, headers=auth_headers(teacher)
    )
    assert r.status_code == 404
    assert (
        client.delete(f"{API}/courses/{theirs['id']}", headers=auth_headers(teacher)).status_code
        == 404
    )

    all_ids = {c["id"] for c in client.get(f"{API}/courses", headers=auth_headers(admin)).json()}
    assert {mine["id"], theirs["id"]} <= all_ids


def test_student_sees_only_enrolled_courses_read_only(client, teacher, student, auth_headers, db):
    enrolled = create_course(client, auth_headers(teacher), code="E1")
    hidden = create_course(client, auth_headers(teacher), code="H1")
    db.add(CourseEnrollment(course_id=enrolled["id"], student_id=student.id))
    db.commit()
    h = auth_headers(student)

    ids = {c["id"] for c in client.get(f"{API}/courses", headers=h).json()}
    assert ids == {enrolled["id"]}
    assert client.get(f"{API}/courses/{enrolled['id']}", headers=h).status_code == 200
    assert client.get(f"{API}/courses/{hidden['id']}", headers=h).status_code == 404
    assert (
        client.patch(f"{API}/courses/{enrolled['id']}", json={"title": "x"}, headers=h).status_code
        == 403
    )
    assert client.delete(f"{API}/courses/{enrolled['id']}", headers=h).status_code == 403


def test_update_course_and_clear_description(client, teacher, auth_headers):
    h = auth_headers(teacher)
    course = create_course(client, h, description="old")
    r = client.patch(
        f"{API}/courses/{course['id']}", json={"title": "New", "description": None}, headers=h
    )
    assert r.status_code == 200
    assert r.json()["title"] == "New" and r.json()["description"] is None
    assert r.json()["code"] == "CS301"


def test_unauthenticated_requests_rejected(client):
    assert client.get(f"{API}/courses").status_code == 401


def test_delete_course_soft_deletes_topics_and_materials(client, teacher, auth_headers, db):
    h = auth_headers(teacher)
    course = create_course(client, h)
    topic = create_topic(client, h, course["id"])
    db.add(
        Material(
            course_id=course["id"],
            topic_id=topic["id"],
            uploaded_by=teacher.id,
            file_name="a.pdf",
            file_type="pdf",
            storage_path="x",
            file_size_bytes=1,
            content_hash="h",
            status=MaterialStatus.UPLOADED,
        )
    )
    db.commit()

    assert client.delete(f"{API}/courses/{course['id']}", headers=h).status_code == 204
    assert client.get(f"{API}/courses/{course['id']}", headers=h).status_code == 404
    assert client.get(f"{API}/courses", headers=h).json() == []
    db.expire_all()
    assert db.get(Course, course["id"]).deleted_at is not None
    assert db.get(Topic, topic["id"]).deleted_at is not None
    assert db.query(Material).filter(Material.deleted_at.is_(None)).count() == 0


# ---- topics ----


def test_create_topics_with_positions_and_subtopics(client, teacher, auth_headers):
    h = auth_headers(teacher)
    course = create_course(client, h)
    a = create_topic(client, h, course["id"], "A")
    b = create_topic(client, h, course["id"], "B")
    sub = create_topic(client, h, course["id"], "A1", parent_topic_id=a["id"])
    assert (a["position"], b["position"], sub["position"]) == (0, 1, 0)
    assert sub["parent_topic_id"] == a["id"]
    listed = client.get(f"{API}/courses/{course['id']}/topics", headers=h).json()
    assert [t["title"] for t in listed] == ["A", "A1", "B"]


def test_duplicate_topic_title_conflicts_case_insensitive_per_parent(client, teacher, auth_headers):
    h = auth_headers(teacher)
    course = create_course(client, h)
    a = create_topic(client, h, course["id"], "Joins")
    r = client.post(f"{API}/courses/{course['id']}/topics", json={"title": "joins"}, headers=h)
    assert r.status_code == 409
    create_topic(client, h, course["id"], "Joins", parent_topic_id=a["id"])


def test_topic_parent_must_be_in_same_course(client, teacher, auth_headers):
    h = auth_headers(teacher)
    c1 = create_course(client, h, code="C1")
    c2 = create_course(client, h, code="C2")
    foreign = create_topic(client, h, c1["id"], "X")
    r = client.post(
        f"{API}/courses/{c2['id']}/topics",
        json={"title": "Y", "parent_topic_id": foreign["id"]},
        headers=h,
    )
    assert r.status_code == 422


def test_topic_permissions(client, teacher, other_teacher, student, auth_headers, db):
    h = auth_headers(teacher)
    course = create_course(client, h)
    topic = create_topic(client, h, course["id"])
    foreign_h = auth_headers(other_teacher)

    assert client.get(f"{API}/courses/{course['id']}/topics", headers=foreign_h).status_code == 404
    r = client.post(f"{API}/courses/{course['id']}/topics", json={"title": "Z"}, headers=foreign_h)
    assert r.status_code == 404
    assert (
        client.patch(
            f"{API}/topics/{topic['id']}", json={"title": "Z"}, headers=foreign_h
        ).status_code
        == 404
    )
    assert client.delete(f"{API}/topics/{topic['id']}", headers=foreign_h).status_code == 404

    db.add(CourseEnrollment(course_id=course["id"], student_id=student.id))
    db.commit()
    sh = auth_headers(student)
    assert client.get(f"{API}/courses/{course['id']}/topics", headers=sh).status_code == 200
    assert (
        client.post(
            f"{API}/courses/{course['id']}/topics", json={"title": "Z"}, headers=sh
        ).status_code
        == 403
    )
    assert (
        client.patch(f"{API}/topics/{topic['id']}", json={"title": "Z"}, headers=sh).status_code
        == 403
    )


def test_rename_topic_and_conflict_with_sibling(client, teacher, auth_headers):
    h = auth_headers(teacher)
    course = create_course(client, h)
    a = create_topic(client, h, course["id"], "A")
    create_topic(client, h, course["id"], "B")
    assert (
        client.patch(f"{API}/topics/{a['id']}", json={"title": "A2"}, headers=h).json()["title"]
        == "A2"
    )
    assert (
        client.patch(f"{API}/topics/{a['id']}", json={"title": "b"}, headers=h).status_code == 409
    )
    assert (
        client.patch(f"{API}/topics/{a['id']}", json={"title": "A2"}, headers=h).status_code == 200
    )


def test_delete_topic_cascades_to_subtopics_and_frees_title(client, teacher, auth_headers):
    h = auth_headers(teacher)
    course = create_course(client, h)
    a = create_topic(client, h, course["id"], "A")
    create_topic(client, h, course["id"], "A1", parent_topic_id=a["id"])
    keep = create_topic(client, h, course["id"], "Keep")
    assert client.delete(f"{API}/topics/{a['id']}", headers=h).status_code == 204
    listed = client.get(f"{API}/courses/{course['id']}/topics", headers=h).json()
    assert [t["id"] for t in listed] == [keep["id"]]
    create_topic(client, h, course["id"], "A")


def test_reorder_topics(client, teacher, auth_headers):
    h = auth_headers(teacher)
    course = create_course(client, h)
    a = create_topic(client, h, course["id"], "A")
    b = create_topic(client, h, course["id"], "B")
    r = client.put(
        f"{API}/courses/{course['id']}/topics/order",
        json={"items": [{"id": a["id"], "position": 1}, {"id": b["id"], "position": 0}]},
        headers=h,
    )
    assert r.status_code == 200
    assert [t["title"] for t in r.json()] == ["B", "A"]


def test_reorder_rejects_foreign_topic(client, teacher, auth_headers):
    h = auth_headers(teacher)
    c1 = create_course(client, h, code="C1")
    c2 = create_course(client, h, code="C2")
    foreign = create_topic(client, h, c2["id"], "F")
    r = client.put(
        f"{API}/courses/{c1['id']}/topics/order",
        json={"items": [{"id": foreign["id"], "position": 0}]},
        headers=h,
    )
    assert r.status_code == 422
