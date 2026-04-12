from sqlalchemy.orm import Session
from app.repositories import UserRepository
from app.core.security import get_password_hasher


class AuthService:
    """Authentication service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.hasher = get_password_hasher()
    
    def authenticate_user(self, username: str, password: str):
        """Authenticate user by username and password"""
        user = self.user_repo.get_by_username(username)
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not self.hasher.verify_password(password, user.password_hash):
            return None
        
        return user
