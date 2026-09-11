from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core import get_db
from app.core.auth import require_authenticated_user, establish_session
from app.services.auth_rate_limit_service import AuthRateLimitService
from app.schemas import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    SetupStatusResponse,
    TopAdminSetupRequest,
    PasswordResetRequestRequest,
    PasswordResetConfirmRequest,
)
from app.services import AuthService, PasswordResetService
from app.services import UserService
from app.services.app_settings_service import AppSettingsService
from app.repositories import UserRepository

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/setup-status", response_model=SetupStatusResponse)
@router.get("/setup-status/", response_model=SetupStatusResponse)
async def get_setup_status(
    db: Session = Depends(get_db),
):
    user_repo = UserRepository(db)
    top_admin_exists = user_repo.has_top_admin()
    # The first-start decision must not depend on optional application or SMTP
    # settings.  On an empty database the setup wizard can therefore start even
    # while those settings are still being initialized.
    if not top_admin_exists:
        return SetupStatusResponse(
            setup_required=True,
            top_admin_exists=False,
            top_admin_reset_email_channel_configured=False,
        )

    top_admin = user_repo.get_top_admin()
    email_settings = AppSettingsService(db).get_email_settings()

    smtp_host = (email_settings.get("smtp_host") or "").strip()
    email_sender = (email_settings.get("email_sender") or "").strip()
    email_enabled = bool(email_settings.get("email_enabled"))
    top_admin_email = (getattr(top_admin, "email", None) or "").strip()

    reset_email_channel_configured = bool(
        top_admin_email and email_enabled and smtp_host and email_sender
    )

    return SetupStatusResponse(
        setup_required=not top_admin_exists,
        top_admin_exists=top_admin_exists,
        top_admin_reset_email_channel_configured=reset_email_channel_configured,
    )


@router.post("/setup-top-admin", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
@router.post("/setup-top-admin/", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def setup_top_admin(
    setup_data: TopAdminSetupRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # Serialize the one-time setup across workers.  The lock lives until the
    # audited creation commits or rolls back and is a no-op for local SQLite.
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 824_231_701})
    if UserRepository(db).has_top_admin():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Top-Admin wurde bereits eingerichtet",
        )

    try:
        user = UserService(db).create_top_admin(
            setup_data.username,
            setup_data.email,
            setup_data.password,
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Benutzername oder E-Mail existiert bereits",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    establish_session(request, user)

    return LoginResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        message="Top-Admin erfolgreich eingerichtet",
    )


@router.post("/login", response_model=LoginResponse)
@router.post("/login/", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Login with username and password"""
    if not UserRepository(db).has_top_admin():
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ersteinrichtung erforderlich. Bitte zuerst den TopAdmin anlegen.",
        )

    limiter = AuthRateLimitService(db)
    limiter.enforce("login_ip", request.client.host if request.client else "unknown", 30, 60)
    limiter.enforce("login_account", login_data.username.strip().casefold(), 5, 60)
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(login_data.username, login_data.password)

    if not user:
        # Anforderung 1: Nach 5 aufeinanderfolgenden Fehlversuchen beim Login des TopAdmin
        # muss das Frontend automatisch das nicht schließbare Reset-Modal öffnen können.
        # Der Zähler wird ausschließlich für TopAdmin-Konten geführt.
        reset_available = PasswordResetService(db).register_failed_login(login_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Invalid username or password",
                "top_admin_reset_available": reset_available,
            },
        )

    PasswordResetService(db).register_successful_login(user)

    # Create session
    establish_session(request, user)

    return LoginResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        message="Login successful"
    )


@router.post("/login-kasse", response_model=LoginResponse)
@router.post("/login-kasse/", response_model=LoginResponse)
async def login_kasse(
    request: Request,
    db: Session = Depends(get_db),
):
    """Direct login for the hidden cash register account."""
    if not UserRepository(db).has_top_admin():
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ersteinrichtung erforderlich. Bitte zuerst den TopAdmin anlegen.",
        )

    app_settings = AppSettingsService(db).get_or_create_settings()
    if app_settings.kasse_direct_login_enabled is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Direktanmeldung als Kasse ist deaktiviert",
        )

    user = UserService(db).ensure_kasse_user()

    establish_session(request, user)

    return LoginResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        message="Kasse angemeldet",
    )


@router.post("/password-reset/request")
@router.post("/password-reset/request/")
async def request_password_reset(
    payload: PasswordResetRequestRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Schritt 1 des TopAdmin-Self-Service-Resets.

    Antwortet absichtlich immer mit derselben generischen Erfolgsmeldung, unabhängig davon,
    ob die eingegebene E-Mail mit der hinterlegten TopAdmin-E-Mail übereinstimmt - so lässt
    sich über diesen Endpunkt nicht erschließen, ob/welche E-Mail hinterlegt ist. Nur bei
    exakter Übereinstimmung wird tatsächlich ein Reset-Token erzeugt und eine E-Mail versendet.
    """
    # Die Reset-Seite wird vom selben Origin ausgeliefert wie das Backend (siehe
    # docker-compose.yml: das gebaute Vue-Frontend wird aus dem Backend-Container bedient),
    # daher genügt request.base_url zum Aufbau des absoluten Links.
    reset_url_base = f"{str(request.base_url).rstrip('/')}/password-reset/"
    PasswordResetService(db).request_reset(
        payload.email,
        reset_url_base=reset_url_base,
        requested_ip=request.client.host if request.client else None,
    )
    return {
        "message": "Falls die E-Mail-Adresse hinterlegt ist, wurde ein Link zum Zurücksetzen des Passworts versendet.",
    }


@router.post("/password-reset/confirm")
@router.post("/password-reset/confirm/")
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Schritt 2: neues Passwort mit dem per E-Mail erhaltenen, einmaligen Token setzen."""
    AuthRateLimitService(db).enforce("reset_confirm_ip", request.client.host if request.client else "unknown", 10, 60)
    try:
        PasswordResetService(db).confirm_reset(payload.token, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"message": "Passwort wurde erfolgreich zurückgesetzt. Du kannst dich jetzt anmelden."}


@router.post("/logout")
@router.post("/logout/")
async def logout(request: Request):
    """Logout"""
    request.session.clear()
    return {"message": "Logged out successfully"}


@router.get("/usernames", response_model=list[str])
@router.get("/usernames/", response_model=list[str])
async def get_login_usernames(
    request: Request,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
):
    """Return usernames of known, non-hidden users.

    This endpoint is used when the Kasse user (or any authenticated user) wants
    to switch to a different account. It requires authentication so that username
    suggestions are not publicly exposed, but does not require elevated roles.
    """
    require_authenticated_user(request, db)
    users = UserRepository(db).get_visible_users(include_inactive=include_inactive)
    return [u.username for u in users]


@router.get("/me", response_model=UserResponse)
@router.get("/me/", response_model=UserResponse)
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get current user info"""
    return require_authenticated_user(request, db)
