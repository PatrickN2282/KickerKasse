from app.core.atomic import audited_change
import secrets
from sqlalchemy.orm import Session
from app.repositories import UserRepository
from app.models import (
    Member,
    UserRole,
)
from app.models.user import parse_user_role


class UserService:
    """User management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    @staticmethod
    def _snapshot_user(user) -> dict:
        return {
            "username": user.username,
            "email": user.email,
            "role": getattr(user.role, "value", user.role),
            "is_active": user.is_active,
            "member_id": user.member_id,
        }

    def _audit(
        self,
        action: str,
        user,
        performed_by_username: str | None,
        *,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        from app.services.audit_log_service import AuditLogService

        AuditLogService(self.db).log(
            entity_type="user",
            action=action,
            user_username=performed_by_username,
            entity_id=user.id,
            entity_name=user.username,
            old_value=old_value,
            new_value=new_value,
        )
        self.db.commit()


    @audited_change
    def create_user(
        self,
        username: str,
        email: str | None,
        password: str,
        role: str = "VERKAUF",
        *,
        performed_by_username: str | None = None,
    ):
        """Create a new user"""
        normalized_role = parse_user_role(role)
        if normalized_role == UserRole.TOP_ADMIN.value:
            raise ValueError("Top-Admin kann nur über den initialen Setup-Flow erstellt werden")

        # Check if user already exists
        existing_user = self.repo.get_by_username(username)
        if existing_user:
            if existing_user.is_active:
                raise ValueError(f"User {username} already exists")
            raise ValueError(
                "Es existiert bereits ein deaktivierter Benutzer mit diesem Namen. "
                "Das Benutzerkonto muss reaktiviert werden."
            )
        if email:
            existing_email_user = self.repo.get_by_email(email)
            if existing_email_user:
                if existing_email_user.is_active:
                    raise ValueError(f"Email {email} already in use")
                raise ValueError(
                    "Die E-Mail-Adresse gehört zu einem deaktivierten Benutzer. "
                    "Das Benutzerkonto muss reaktiviert werden."
                )

        user = self.repo.create(username, email, password, role)
        self._audit("CREATED", user, performed_by_username, new_value=self._snapshot_user(user))
        return user

    @audited_change
    def create_top_admin(self, username: str, email: str | None, password: str):
        """Create the single top admin account during initial setup."""
        if self.repo.has_top_admin():
            raise ValueError("Top-Admin existiert bereits")
        if self.repo.get_by_username(username):
            raise ValueError(f"User {username} already exists")
        if email and self.repo.get_by_email(email):
            raise ValueError(f"Email {email} already in use")

        user = self.repo.create(username, email, password, UserRole.TOP_ADMIN.value)
        self._audit("CREATED", user, username, new_value=self._snapshot_user(user))
        return user
    
    def get_user(self, user_id: int):
        """Get user by ID"""
        return self.repo.get_by_id(user_id)
    
    def get_all_users(self, *, include_inactive: bool = False):
        """Get all users"""
        return self.repo.get_visible_users(include_inactive=include_inactive)

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
            Member.archived_at.is_(None),
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
                existing_user = self.repo.update(
                    existing_user.id,
                    role=UserRole.VERKAUF,
                    is_active=True,
                    email=None,
                )

            # A cookie from an earlier installation must not match the newly
            # initialized cash-register account merely because its ID is reused.
            if not self.repo.has_top_admin():
                existing_user.session_version = secrets.randbelow(2_000_000_000) + 1
                self.db.commit()
                self.db.refresh(existing_user)
            return existing_user

        user = self.repo.create(
            username="Kasse",
            email=None,
            password=secrets.token_urlsafe(24),
            role=UserRole.VERKAUF.value,
            is_active=True,
        )
        if not self.repo.has_top_admin():
            user.session_version = secrets.randbelow(2_000_000_000) + 1
            self.db.commit()
            self.db.refresh(user)
        return user
    
    @staticmethod
    def _validate_management_target(user, *, password_only: bool = False, current_user_id: int | None = None, deactivating: bool = False):
        if user.role == UserRole.TOP_ADMIN:
            raise ValueError("Top-Admin kann nicht über die Benutzerverwaltung geändert werden")
        if deactivating and user.id == current_user_id:
            raise ValueError("Du kannst dein eigenes Konto nicht deaktivieren")
        if user.member_id is not None and not password_only:
            raise ValueError("Mitgliedskonten werden über die Rollenvergabe der Mitgliederverwaltung verwaltet")

    @audited_change
    def update_user(self, user_id: int, *, performed_by_username: str | None = None, **kwargs):
        """Update user"""
        user = self.repo.get_by_id(user_id)
        if not user:
            return None

        self._validate_management_target(user, password_only=set(kwargs) <= {"password"})
        if set(kwargs) - {"username", "email", "role", "password"}:
            raise ValueError("Kontozustand und Verknüpfung dürfen nicht über allgemeine Benutzerupdates geändert werden")

        old_snapshot = self._snapshot_user(user)

        username = kwargs.get("username")
        if username:
            existing_user = self.repo.get_by_username(username)
            if existing_user and existing_user.id != user_id:
                raise ValueError(f"User {username} already exists")

        role = parse_user_role(kwargs.get("role"))
        if role == UserRole.TOP_ADMIN.value:
            raise ValueError("Top-Admin kann nicht über die Benutzerverwaltung vergeben werden")

        if "email" in kwargs and kwargs["email"]:
            existing_user = self.repo.get_by_email(kwargs["email"])
            if existing_user and existing_user.id != user_id:
                raise ValueError(f"Email {kwargs['email']} already in use")

        updated_user = self.repo.update(user_id, **kwargs)
        if updated_user:
            self._audit(
                "UPDATED",
                updated_user,
                performed_by_username,
                old_value=old_snapshot,
                new_value={**self._snapshot_user(updated_user), "password_changed": "password" in kwargs},
            )
        return updated_user
    
    @audited_change
    def deactivate_user(
        self,
        user_id: int,
        *,
        current_user_id: int | None = None,
        performed_by_username: str | None = None,
    ):
        """Deactivate a user."""
        user = self.repo.get_by_id(user_id)
        if not user:
            return False
        self._validate_management_target(user, current_user_id=current_user_id, deactivating=True)
        if not user.is_active:
            return True

        old_snapshot = self._snapshot_user(user)
        updated_user = self.repo.update(user.id, is_active=False, email=None)
        if updated_user:
            self._audit(
                "UPDATED",
                updated_user,
                performed_by_username,
                old_value=old_snapshot,
                new_value=self._snapshot_user(updated_user),
            )
            return True
        return False

    @audited_change
    def reactivate_user(
        self,
        user_id: int,
        *,
        performed_by_username: str | None = None,
    ):
        """Reactivate a previously deactivated user."""
        user = self.repo.get_by_id(user_id)
        if not user:
            return None
        self._validate_management_target(user)
        if user.is_active:
            return user

        old_snapshot = self._snapshot_user(user)
        updated_user = self.repo.update(user.id, is_active=True)
        if updated_user:
            self._audit(
                "UPDATED",
                updated_user,
                performed_by_username,
                old_value=old_snapshot,
                new_value=self._snapshot_user(updated_user),
            )
        return updated_user
