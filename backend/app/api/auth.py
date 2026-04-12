from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from app.core import get_db
from app.schemas import LoginRequest, LoginResponse, UserResponse
from app.services import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
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


@router.post("/logout")
async def logout(request: Request):
    """Logout"""
    request.session.clear()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
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
