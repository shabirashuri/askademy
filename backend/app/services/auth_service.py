import time
from collections import defaultdict, deque

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import TooManyRequests, Unauthorized
from app.core.security import create_access_token, verify_password
from app.models.user import User

_attempts: dict[str, deque[float]] = defaultdict(deque)


def _check_throttle(key: str) -> None:
    now = time.monotonic()
    window = _attempts[key]
    while window and now - window[0] > settings.login_window_seconds:
        window.popleft()
    if len(window) >= settings.login_max_attempts:
        raise TooManyRequests("Too many login attempts. Try again later.")


def reset_throttle() -> None:
    _attempts.clear()


def authenticate(db: Session, email: str, password: str, client_ip: str = "") -> User:
    key = f"{client_ip}|{email.lower()}"
    _check_throttle(key)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        _attempts[key].append(time.monotonic())
        raise Unauthorized("Invalid email or password.")
    _attempts.pop(key, None)
    return user


def issue_token(user: User) -> str:
    return create_access_token(str(user.id))
