from datetime import timedelta

from app.core.security import create_access_token
from app.models.user import UserRole


def test_login_success_returns_token_and_user(client, make_user):
    user = make_user(email="t@example.com")
    r = client.post(
        "/api/v1/auth/login", json={"email": "t@example.com", "password": "password123"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["id"] == str(user.id)
    assert "password_hash" not in body["user"]


def test_login_email_is_case_insensitive(client, make_user):
    make_user(email="mixed@example.com")
    r = client.post(
        "/api/v1/auth/login", json={"email": "MIXED@example.com", "password": "password123"}
    )
    assert r.status_code == 200


def test_login_wrong_password_is_401(client, make_user):
    make_user(email="t@example.com")
    r = client.post("/api/v1/auth/login", json={"email": "t@example.com", "password": "nope"})
    assert r.status_code == 401
    assert r.json()["code"] == "unauthorized"


def test_login_inactive_user_rejected(client, make_user):
    make_user(email="off@example.com", is_active=False)
    r = client.post(
        "/api/v1/auth/login", json={"email": "off@example.com", "password": "password123"}
    )
    assert r.status_code == 401


def test_login_is_throttled_after_repeated_failures(client, make_user):
    make_user(email="t@example.com")
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"email": "t@example.com", "password": "bad"})
    r = client.post(
        "/api/v1/auth/login", json={"email": "t@example.com", "password": "password123"}
    )
    assert r.status_code == 429


def test_me_requires_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_with_valid_token(client, make_user, auth_headers):
    user = make_user()
    r = client.get("/api/v1/auth/me", headers=auth_headers(user))
    assert r.status_code == 200 and r.json()["email"] == user.email


def test_expired_and_garbage_tokens_rejected(client, make_user):
    user = make_user()
    expired = create_access_token(str(user.id), timedelta(seconds=-5))
    for token in (expired, "garbage"):
        r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401


def test_deactivated_user_token_rejected(client, make_user, auth_headers, db):
    user = make_user()
    headers = auth_headers(user)
    user.is_active = False
    db.commit()
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_admin_creates_user_and_duplicate_conflicts(client, make_user, auth_headers):
    admin = make_user(UserRole.ADMIN)
    payload = {
        "email": "new@example.com",
        "full_name": "New",
        "password": "password123",
        "role": "student",
    }
    r = client.post("/api/v1/users", json=payload, headers=auth_headers(admin))
    assert r.status_code == 201 and r.json()["role"] == "student"
    r = client.post("/api/v1/users", json=payload, headers=auth_headers(admin))
    assert r.status_code == 409


def test_non_admin_cannot_create_users(client, make_user, auth_headers):
    payload = {
        "email": "x@example.com",
        "full_name": "X",
        "password": "password123",
        "role": "teacher",
    }
    for role in (UserRole.TEACHER, UserRole.STUDENT):
        r = client.post("/api/v1/users", json=payload, headers=auth_headers(make_user(role)))
        assert r.status_code == 403


def test_teacher_lists_only_students(client, make_user, auth_headers):
    teacher = make_user(UserRole.TEACHER)
    make_user(UserRole.STUDENT)
    make_user(UserRole.ADMIN)
    r = client.get("/api/v1/users?role=admin", headers=auth_headers(teacher))
    assert r.status_code == 200
    assert {u["role"] for u in r.json()} == {"student"}


def test_student_cannot_list_users(client, make_user, auth_headers):
    r = client.get("/api/v1/users", headers=auth_headers(make_user(UserRole.STUDENT)))
    assert r.status_code == 403


def test_admin_can_deactivate_user(client, make_user, auth_headers):
    admin, target = make_user(UserRole.ADMIN), make_user(UserRole.STUDENT)
    r = client.patch(
        f"/api/v1/users/{target.id}", json={"is_active": False}, headers=auth_headers(admin)
    )
    assert r.status_code == 200 and r.json()["is_active"] is False


def test_teacher_adds_student_but_not_other_roles(client, make_user, auth_headers):
    teacher = auth_headers(make_user(UserRole.TEACHER))

    def body(role, email):
        return {"email": email, "full_name": "New", "password": "password123", "role": role}

    r = client.post(
        "/api/v1/users", json=body("student", "ok-student@example.com"), headers=teacher
    )
    assert r.status_code == 201 and r.json()["role"] == "student"
    for role in ("teacher", "admin"):
        r = client.post("/api/v1/users", json=body(role, f"{role}-x@example.com"), headers=teacher)
        assert r.status_code == 403, role
    r = client.post(
        "/api/v1/users", json=body("student", "ok-student@example.com"), headers=teacher
    )
    assert r.status_code == 409


def test_student_cannot_add_students(client, make_user, auth_headers):
    payload = {
        "email": "s2@example.com",
        "full_name": "S",
        "password": "password123",
        "role": "student",
    }
    r = client.post(
        "/api/v1/users", json=payload, headers=auth_headers(make_user(UserRole.STUDENT))
    )
    assert r.status_code == 403
