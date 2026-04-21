from sqlalchemy.orm import Session
from app.repositories import UserRepository


class UserService:
    """User management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)
    
    def create_user(self, username: str, email: str | None, password: str, role: str = "VERKAUF"):
        """Create a new user"""
        # Check if user already exists
        if self.repo.get_by_username(username):
            raise ValueError(f"User {username} already exists")
        if email and self.repo.get_by_email(email):
            raise ValueError(f"Email {email} already in use")
        
        return self.repo.create(username, email, password, role)
    
    def get_user(self, user_id: int):
        """Get user by ID"""
        return self.repo.get_by_id(user_id)
    
    def get_all_users(self):
        """Get all users"""
        return self.repo.get_all()
    
    def update_user(self, user_id: int, **kwargs):
        """Update user"""
        user = self.repo.get_by_id(user_id)
        if not user:
            return None

        username = kwargs.get("username")
        if username:
            existing_user = self.repo.get_by_username(username)
            if existing_user and existing_user.id != user_id:
                raise ValueError(f"User {username} already exists")

        if "email" in kwargs and kwargs["email"]:
            existing_user = self.repo.get_by_email(kwargs["email"])
            if existing_user and existing_user.id != user_id:
                raise ValueError(f"Email {kwargs['email']} already in use")

        return self.repo.update(user_id, **kwargs)
    
    def delete_user(self, user_id: int):
        """Delete user"""
        return self.repo.delete(user_id)
