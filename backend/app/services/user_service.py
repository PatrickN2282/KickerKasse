from sqlalchemy.orm import Session
from app.repositories import UserRepository
from app.models import Member


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

    def get_finance_options(self):
        """Get finance actor options from users and role-based members."""
        options = []

        for user in self.repo.get_all_active():
            display_name = user.member.name if getattr(user, "member", None) else user.username
            options.append({
                "id": f"user-{user.id}",
                "username": display_name,
                "role": user.role,
                "member_id": user.member_id,
                "source": "member" if user.member_id else "user",
            })

        members_with_roles = self.db.query(Member).filter(Member.role.is_not(None)).all()
        for member in members_with_roles:
            linked_user = getattr(member, "linked_user", None)
            if linked_user and linked_user.is_active:
                continue

            options.append({
                "id": f"member-{member.id}",
                "username": member.name,
                "role": member.role,
                "member_id": member.id,
                "source": "member",
            })

        return sorted(options, key=lambda option: (option["username"] or "").lower())
    
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
