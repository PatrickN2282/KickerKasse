from .config import settings
from .database import engine, SessionLocal, get_db
from .security import PasswordHasher, get_password_hasher


def __getattr__(name):
    """Load auth helpers lazily to avoid a repositories/core import cycle."""
    if name in {"get_current_user", "require_auth", "require_admin"}:
        from . import auth

        return getattr(auth, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "settings",
    "engine",
    "SessionLocal",
    "get_db",
    "PasswordHasher",
    "get_password_hasher",
    "get_current_user",
    "require_auth",
    "require_admin",
]
