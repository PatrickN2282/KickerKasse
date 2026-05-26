from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core import get_db
from app.core.auth import require_authenticated_user
from app.schemas import LoginRequest, LoginResponse, UserResponse, SetupStatusResponse, TopAdminSetupRequest
from app.services import AuthService
from app.services import UserService
from app.repositories import UserRepository

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/setup-status", response_model=SetupStatusResponse)
@router.get("/setup-status/", response_model=SetupStatusResponse)
async def get_setup_status(
    db: Session = Depends(get_db),
):
    top_admin_exists = UserRepository(db).has_top_admin()
    return SetupStatusResponse(
        setup_required=not top_admin_exists,
        top_admin_exists=top_admin_exists,
    )


@router.post("/setup-top-admin", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
@router.post("/setup-top-admin/", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def setup_top_admin(
    setup_data: TopAdminSetupRequest,
    request: Request,
    db: Session = Depends(get_db),
):
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

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role.value

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
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    # Create session
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role.value
    
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
    user = UserService(db).ensure_kasse_user()

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role.value

    return LoginResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        message="Kasse angemeldet",
    )


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
    db: Session = Depends(get_db),
):
    """Return usernames of active, non-hidden users for the login-switch dropdown.

    This endpoint is used when the Kasse user (or any authenticated user) wants
    to switch to a different account. It requires authentication so that username
    suggestions are not publicly exposed, but does not require elevated roles.
    """
    require_authenticated_user(request, db)
    users = UserRepository(db).get_visible_active_users()
    return [u.username for u in users]


@router.get("/me", response_model=UserResponse)
@router.get("/me/", response_model=UserResponse)
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get current user info"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    from app.repositories import UserRepository
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user
