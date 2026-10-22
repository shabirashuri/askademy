"""Seed the first admin account from FIRST_ADMIN_EMAIL / FIRST_ADMIN_PASSWORD (idempotent)."""

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole


def main() -> None:
    if not settings.first_admin_email or not settings.first_admin_password:
        raise SystemExit("Set FIRST_ADMIN_EMAIL and FIRST_ADMIN_PASSWORD first.")
    with SessionLocal() as db:
        if db.scalar(select(User.id).where(User.email == settings.first_admin_email)):
            print("Admin already exists; nothing to do.")
            return
        db.add(
            User(
                email=settings.first_admin_email,
                full_name="Administrator",
                password_hash=hash_password(settings.first_admin_password),
                role=UserRole.ADMIN,
            )
        )
        db.commit()
        print(f"Created admin {settings.first_admin_email}.")


if __name__ == "__main__":
    main()
