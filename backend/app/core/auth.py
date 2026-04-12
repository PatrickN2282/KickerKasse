from fastapi import Request, HTTPException, status
from functools import wraps
from typing import Optional
from sqlalchemy.orm import Session
from app.models import User, UserRole


async def get_current_user(request: Request, db: Session) -> Optional[User]:
    """Get current user from session"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user


def require_auth(f):
    """Require authentication decorator"""
    @wraps(f)
    async def decorated(*args, **kwargs):
        request: Request = kwargs.get("request")
        if not request:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        user_id = request.session.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        return await f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Require admin role decorator"""
    @wraps(f)
    async def decorated(*args, **kwargs):
        request: Request = kwargs.get("request")
        db: Session = kwargs.get("db")
        
        if not request or not db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        user_id = request.session.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return await f(*args, **kwargs)
    return decorated
