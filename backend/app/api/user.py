from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_roles
from app.models import UserRole
from app.schemas import UserCreate, UserResponse, UserUpdate
from app.services import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse])
@router.get("", response_model=list[UserResponse])
async def get_users(
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    return UserService(db).get_all_users()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    service = UserService(db)
    try:
        return service.create_user(
            user_data.username,
            user_data.email,
            user_data.password,
            user_data.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{user_id}", response_model=UserResponse)
@router.get("/{user_id}/", response_model=UserResponse)
async def get_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    user = UserService(db).get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
@router.put("/{user_id}/", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    user = UserService(db).update_user(user_id, **user_data.model_dump(exclude_unset=True))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{user_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    require_roles(request, db, UserRole.ADMIN)
    if not UserService(db).delete_user(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
