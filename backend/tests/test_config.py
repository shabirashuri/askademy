from sqlalchemy.engine import make_url

from app.core.config import Settings


def test_database_url_is_loaded_from_environment(monkeypatch) -> None:
    database_url = (
        "postgresql+psycopg://postgres:example-password"
        "@db.example-project.supabase.co:5432/postgres?sslmode=require"
    )
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings(_env_file=None)
    parsed_url = make_url(settings.database_url)

    assert parsed_url.drivername == "postgresql+psycopg"
    assert parsed_url.host == "db.example-project.supabase.co"
    assert parsed_url.query["sslmode"] == "require"
