from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from app.core import get_db
from app.schemas import UserCreate, UserResponse
from app.services import UserService
from app.models import UserRole

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new user (Admin only)"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    from app.repositories import UserRepository
    current_user = UserRepository(db).get_by_id(user_id)
    if not current_user or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    service = UserService(db)
    try:
        user = service.create_user(
            user_data.username,
            user_data.email,
            user_data.password,
            user_data.role,
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=list[UserResponse])
async def get_users(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get all users (Admin only)"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    from app.repositories import UserRepository
    current_user = UserRepository(db).get_by_id(user_id)
    if not current_user or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    service = UserService(db)
    return service.get_all_users()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get user by ID"""
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    service = UserService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: dict,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update user (Admin only)"""
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    from app.repositories import UserRepository
    current_user = UserRepository(db).get_by_id(current_user_id)
    if not current_user or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    service = UserService(db)
    user = service.update_user(user_id, **user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete user (Admin only)"""
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    from app.repositories import UserRepository
    current_user = UserRepository(db).get_by_id(current_user_id)
    if not current_user or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    service = UserService(db)
    if not service.delete_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
