from sqlalchemy.orm import Session
from app.models import User, UserRole
from app.core.security import get_password_hasher


class UserRepository:
    """Repository for User model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, username: str, email: str, password: str, role: str = "CASHIER") -> User:
        """Create a new user"""
        hasher = get_password_hasher()
        user = User(
            username=username,
            email=email,
            password_hash=hasher.hash_password(password),
            role=UserRole[role.upper()] if isinstance(role, str) else role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> User | None:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> User | None:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self) -> list[User]:
        """Get all users"""
        return self.db.query(User).all()
    
    def update(self, user_id: int, **kwargs) -> User | None:
        """Update user"""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # Handle password update
        if "password" in kwargs:
            hasher = get_password_hasher()
            kwargs["password_hash"] = hasher.hash_password(kwargs.pop("password"))
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """Delete user"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
