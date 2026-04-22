import secrets
from sqlalchemy.orm import Session
from app.repositories import UserRepository
from app.models import Member, Transaction, Voucher, CashEntry, ClubAccountEntry, UserRole


class UserService:
    """User management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)
    
    def create_user(self, username: str, email: str | None, password: str, role: str = "VERKAUF"):
        """Create a new user"""
        normalized_role = getattr(role, "value", role)
        if normalized_role == UserRole.TOP_ADMIN.value:
            raise ValueError("Top-Admin kann nur über den initialen Setup-Flow erstellt werden")

        # Check if user already exists
        if self.repo.get_by_username(username):
            raise ValueError(f"User {username} already exists")
        if email and self.repo.get_by_email(email):
            raise ValueError(f"Email {email} already in use")
        
        return self.repo.create(username, email, password, role)

    def create_top_admin(self, username: str, email: str | None, password: str):
        """Create the single top admin account during initial setup."""
        if self.repo.has_top_admin():
            raise ValueError("Top-Admin existiert bereits")
        if self.repo.get_by_username(username):
            raise ValueError(f"User {username} already exists")
        if email and self.repo.get_by_email(email):
            raise ValueError(f"Email {email} already in use")

        return self.repo.create(username, email, password, UserRole.TOP_ADMIN.value)
    
    def get_user(self, user_id: int):
        """Get user by ID"""
        return self.repo.get_by_id(user_id)
    
    def get_all_users(self):
        """Get all users"""
        return self.repo.get_visible_active_users()

    def get_finance_options(self):
        """Get finance actor options from users and role-based members."""
        options = []

        for user in self.repo.get_visible_finance_users():
            member = getattr(user, "member", None)
            display_name = member.name if member is not None else user.username
            options.append({
                "id": f"user-{user.id}",
                "username": display_name,
                "role": user.role,
                "member_id": user.member_id,
                "source": "member" if user.member_id else "user",
            })

        members_with_roles = self.db.query(Member).filter(
            Member.role.in_([UserRole.TOP_ADMIN, UserRole.ADMIN, UserRole.MANAGER]),
        ).all()
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

    def ensure_kasse_user(self):
        """Ensure the hidden direct-login cash register account exists."""
        existing_user = self.repo.get_by_username("Kasse")
        if existing_user:
            if existing_user.role != UserRole.VERKAUF or not existing_user.is_active:
                return self.repo.update(
                    existing_user.id,
                    role=UserRole.VERKAUF,
                    is_active=True,
                    email=None,
                )
            return existing_user

        return self.repo.create(
            username="Kasse",
            email=None,
            password=secrets.token_urlsafe(24),
            role=UserRole.VERKAUF.value,
            is_active=True,
        )
    
    def update_user(self, user_id: int, **kwargs):
        """Update user"""
        user = self.repo.get_by_id(user_id)
        if not user:
            return None

        if user.role == UserRole.TOP_ADMIN:
            raise ValueError("Top-Admin kann nicht über die Benutzerverwaltung geändert werden")

        username = kwargs.get("username")
        if username:
            existing_user = self.repo.get_by_username(username)
            if existing_user and existing_user.id != user_id:
                raise ValueError(f"User {username} already exists")

        role = getattr(kwargs.get("role"), "value", kwargs.get("role"))
        if role == UserRole.TOP_ADMIN.value:
            raise ValueError("Top-Admin kann nicht über die Benutzerverwaltung vergeben werden")

        if "email" in kwargs and kwargs["email"]:
            existing_user = self.repo.get_by_email(kwargs["email"])
            if existing_user and existing_user.id != user_id:
                raise ValueError(f"Email {kwargs['email']} already in use")

        return self.repo.update(user_id, **kwargs)
    
    def delete_user(self, user_id: int):
        """Soft-delete a user when historical references exist."""
        user = self.repo.get_by_id(user_id)
        if not user:
            return False
        if user.role == UserRole.TOP_ADMIN:
            raise ValueError("Top-Admin kann nicht gelöscht werden")

        has_references = any([
            self.db.query(Transaction.id).filter(Transaction.user_id == user.id).first(),
            self.db.query(CashEntry.id).filter(CashEntry.user_id == user.id).first(),
            self.db.query(ClubAccountEntry.id).filter(ClubAccountEntry.user_id == user.id).first(),
            self.db.query(Voucher.id).filter(Voucher.created_by_user_id == user.id).first(),
            self.db.query(Voucher.id).filter(Voucher.redeemed_by_user_id == user.id).first(),
        ])

        if has_references:
            self.repo.update(user.id, is_active=False, email=None)
            return True

        return self.repo.delete(user_id)
