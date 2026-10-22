import uuid
from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User
from app.models.user import UserRole
from app.services import auth_service

TEST_SCHEMA = "pytest_sandbox"


@pytest.fixture(scope="session")
def engine():
    """Run DB tests in a throwaway schema of the configured Supabase database.

    Only the `pytest_sandbox` schema is created and dropped; real tables are never touched.
    """
    # Extensions are no-ops on Supabase; a fresh database (e.g. CI) needs them before create_all.
    setup_engine = create_engine(settings.database_url)
    with setup_engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    setup_engine.dispose()

    engine = create_engine(
        settings.database_url,
        connect_args={"options": f"-csearch_path={TEST_SCHEMA},public"},
    )
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {TEST_SCHEMA}"))
    Base.metadata.create_all(engine, checkfirst=False)
    yield engine
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
    engine.dispose()


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db
    auth_service.reset_throttle()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    def factory(role: UserRole = UserRole.TEACHER, password: str = "password123", **kw) -> User:
        user = User(
            email=kw.pop("email", f"{uuid.uuid4().hex[:8]}@example.com"),
            full_name=kw.pop("full_name", "Test User"),
            password_hash=hash_password(password),
            role=role,
            **kw,
        )
        db.add(user)
        db.commit()
        return user

    return factory


@pytest.fixture
def auth_headers() -> Callable[[User], dict[str, str]]:
    def factory(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}

    return factory
