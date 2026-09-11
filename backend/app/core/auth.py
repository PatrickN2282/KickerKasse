from fastapi import HTTPException, Request, status, Depends
from sqlalchemy.orm import Session

from app.core.security import get_password_hasher
from app.models import User, UserRole
from app.repositories import UserRepository


ROLE_ADMIN_PANEL = {UserRole.ADMIN, UserRole.MANAGER}
ROLE_FINANCE = {UserRole.ADMIN, UserRole.MANAGER}
ROLE_MEMBER_MANAGEMENT = {UserRole.ADMIN, UserRole.MANAGER}


def establish_session(request: Request, user: User) -> None:
    request.session.clear()
    request.session.update(user_id=user.id, username=user.username, role=user.role.value, session_version=user.session_version)


async def get_current_user(request: Request, db: Session) -> User | None:
    try:
        return require_authenticated_user(request, db)
    except HTTPException:
        return None


def require_authenticated_user(request: Request, db: Session) -> User:
    user_repo = UserRepository(db)
    if not user_repo.has_top_admin():
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ersteinrichtung erforderlich. Bitte zuerst den TopAdmin anlegen.",
        )

    user_id = request.session.get("user_id")
    user = user_repo.get_by_id(user_id) if user_id else None
    if (not user or not user.is_active
            or request.session.get("session_version") != user.session_version):
        request.session.clear()
        raise HTTPException(status_code=401, detail="Sitzung abgelaufen. Bitte erneut anmelden.")
    return user


def has_any_role(user: User, *roles: UserRole) -> bool:
    if user.role == UserRole.TOP_ADMIN:
        return True
    return user.role in set(roles)


def require_top_admin(request: Request, db: Session) -> User:
    return require_roles(request, db, UserRole.TOP_ADMIN)


def require_roles(request: Request, db: Session, *roles: UserRole) -> User:
    user = require_authenticated_user(request, db)
    if roles and not has_any_role(user, *roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return user


def require_password_confirmation(user: User, password: str | None, db: Session | None = None) -> None:
    from app.services.password_reset_service import PasswordResetService

    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password confirmation required",
        )

    if db is not None:
        from app.services.auth_rate_limit_service import AuthRateLimitService
        AuthRateLimitService(db).check("confirmation", str(user.id), 5, 60)

    if not get_password_hasher().verify_password(password, user.password_hash):
        if db is not None:
            AuthRateLimitService(db).consume("confirmation", str(user.id), 5, 60)
        reset_available = False
        if db is not None and user.role == UserRole.TOP_ADMIN:
            reset_available = PasswordResetService(db).register_failed_login(user.username)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Password confirmation failed",
                "top_admin_reset_available": reset_available,
            },
        )


def resolve_confirmation_user(
    db: Session,
    current_user: User,
    password: str | None,
    *,
    username: str | None = None,
    allow_top_admin_override: bool = False,
) -> User:
    requested_username = (username or "").strip()
    current_username = (current_user.username or "").strip()
    if not requested_username or requested_username.casefold() == current_username.casefold():
        require_password_confirmation(current_user, password, db)
        return current_user

    if not allow_top_admin_override:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Abweichende Zugangsdaten sind für diese Aktion nicht erlaubt",
        )

    override_user = UserRepository(db).get_by_username(requested_username)
    if not override_user or not override_user.is_active or override_user.role != UserRole.TOP_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur der Top-Admin darf diese Aktion mit abweichenden Zugangsdaten freigeben",
        )

    require_password_confirmation(override_user, password, db)
    return override_user


def require_auth(f):
    async def decorated(*args, **kwargs):
        request: Request = kwargs.get("request")
        db: Session = kwargs.get("db")
        if not request or not db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        require_authenticated_user(request, db)
        return await f(*args, **kwargs)
    return decorated


def require_admin(f):
    async def decorated(*args, **kwargs):
        request: Request = kwargs.get("request")
        db: Session = kwargs.get("db")
        if not request or not db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        require_roles(request, db, UserRole.ADMIN)
        return await f(*args, **kwargs)
    return decorated


from app.core.database import get_db

def require_session(request: Request, db: Session = Depends(get_db)) -> User:
    return require_authenticated_user(request, db)
