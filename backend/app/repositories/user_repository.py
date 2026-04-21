from sqlalchemy.orm import Session
from app.models import User, UserRole
from app.models.user import parse_user_role
from app.core.security import get_password_hasher


class UserRepository:
    """Repository for User model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def _normalize_email(email: str | None) -> str | None:
        if email is None:
            return None
        email = email.strip()
        return email or None

    def create(
        self,
        username: str,
        email: str | None,
        password: str,
        role: str = "VERKAUF",
        *,
        member_id: int | None = None,
        is_active: bool = True,
    ) -> User:
        """Create a new user"""
        hasher = get_password_hasher()
        user = User(
            username=username,
            email=self._normalize_email(email),
            password_hash=hasher.hash_password(password),
            role=parse_user_role(role, default=UserRole.VERKAUF),
            member_id=member_id,
            is_active=is_active,
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
    
    def get_by_email(self, email: str | None) -> User | None:
        """Get user by email"""
        email = self._normalize_email(email)
        if not email:
            return None
        return self.db.query(User).filter(User.email == email).first()

    def get_by_member_id(self, member_id: int) -> User | None:
        """Get user linked to a member"""
        return self.db.query(User).filter(User.member_id == member_id).first()

    def get_all(self) -> list[User]:
        """Get all users"""
        return self.db.query(User).all()

    def get_all_active(self) -> list[User]:
        """Get all active users"""
        return self.db.query(User).filter(User.is_active.is_(True)).all()
    
    def update(self, user_id: int, **kwargs) -> User | None:
        """Update user"""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # Handle password update
        if "password" in kwargs:
            hasher = get_password_hasher()
            kwargs["password_hash"] = hasher.hash_password(kwargs.pop("password"))

        if "email" in kwargs:
            kwargs["email"] = self._normalize_email(kwargs["email"])

        for key, value in kwargs.items():
            if hasattr(user, key):
                if key == "role":
                    value = parse_user_role(value, default=user.role)
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
