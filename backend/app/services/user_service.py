from sqlalchemy.orm import Session
from app.repositories import UserRepository


class UserService:
    """User management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)
    
    def create_user(self, username: str, email: str, password: str, role: str = "CASHIER"):
        """Create a new user"""
        # Check if user already exists
        if self.repo.get_by_username(username):
            raise ValueError(f"User {username} already exists")
        if self.repo.get_by_email(email):
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
        return self.repo.update(user_id, **kwargs)
    
    def delete_user(self, user_id: int):
        """Delete user"""
        return self.repo.delete(user_id)
