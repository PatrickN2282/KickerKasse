"""TopAdmin Self-Service-Passwort-Reset (siehe Roadmap-UX-Sicherheit.md, Punkt 1).

Ablauf:
  1. Nach 5 aufeinanderfolgenden Login-Fehlversuchen des TopAdmin bietet das Frontend den
     Reset-Dialog an (`register_failed_login` liefert das Signal dafür).
  2. Der Benutzer bestätigt die hinterlegte E-Mail-Adresse exakt (`request_reset`).
  3. Bei exakter Übereinstimmung wird ein einmaliges, zeitlich begrenztes Token erzeugt und
     per E-Mail versendet (nur der hier erzeugte Klartext-Token verlässt den Server per Mail -
     gespeichert wird ausschließlich ein SHA-256-Hash davon).
  4. Über die Reset-Seite kann mit dem Token ein neues Passwort gesetzt werden
     (`confirm_reset`). Das Token wird dabei sofort ungültig (`used_at` gesetzt).

Alle Schritte werden im bestehenden Audit-Log protokolliert.
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import PasswordResetToken, User, UserRole
from app.repositories import UserRepository
from app.services.audit_log_service import AuditLogService
from app.services.email_service import EmailService
from app.services.auth_rate_limit_service import AuthRateLimitService

logger = logging.getLogger(__name__)

FAILED_LOGIN_THRESHOLD = 5
TOKEN_TTL_MINUTES = 60


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class PasswordResetService:
    """Verwaltet Login-Fehlversuchszähler und den TopAdmin-Passwort-Reset-Flow."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit = AuditLogService(db)

    # ------------------------------------------------------------------
    # Fehlversuchszähler
    # ------------------------------------------------------------------
    def register_failed_login(self, username: str) -> bool:
        """Increments the failed-login counter for a TopAdmin account.

        Returns True once the configured threshold has been reached, signalling that the
        frontend should offer the self-service reset dialog.
        """
        user = self.user_repo.get_by_username(username)
        if not user or user.role != UserRole.TOP_ADMIN:
            return False

        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        self.db.commit()
        self.db.refresh(user)
        return user.failed_login_attempts >= FAILED_LOGIN_THRESHOLD

    def register_successful_login(self, user: User) -> None:
        if user.failed_login_attempts:
            user.failed_login_attempts = 0
            self.db.commit()

    # ------------------------------------------------------------------
    # Reset-Anforderung
    # ------------------------------------------------------------------
    def request_reset(self, email: str, *, reset_url_base: str, requested_ip: str | None = None) -> None:
        """Validates the confirmed email against the TopAdmin account and, on an exact
        match, issues a reset token and sends the reset email.

        `reset_url_base` is the absolute URL prefix (including trailing slash) of the
        dedicated frontend reset page; the raw token is appended to build the final link,
        e.g. "https://kasse.example.org/password-reset/" + token.

        Always logs the attempt. Does not raise on a mismatch so callers can respond with a
        generic message and avoid revealing whether the provided email exists.
        """
        limiter = AuthRateLimitService(self.db)
        if limiter.consume("reset_ip", requested_ip or "unknown", 5, 60):
            return
        if limiter.consume("reset_email", (email or "").strip().casefold(), 1, 60):
            return
        top_admin = self.user_repo.get_top_admin()
        normalized_email = (email or "").strip()

        match = bool(top_admin and top_admin.is_active and top_admin.email and top_admin.email.strip().lower() == normalized_email.lower())

        self.audit.log(
            entity_type="auth",
            action="PASSWORD_RESET_REQUESTED",
            user_username=top_admin.username if top_admin else None,
            entity_id=top_admin.id if top_admin else None,
            entity_name=top_admin.username if top_admin else None,
            new_value={"email_matched": match, "requested_ip": requested_ip},
        )
        self.db.commit()

        if not match:
            logger.info("Password reset requested with non-matching email for TopAdmin account")
            return

        raw_token = secrets.token_urlsafe(32)
        token = PasswordResetToken(
            user_id=top_admin.id,
            token_hash=_hash_token(raw_token),
            expires_at=datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MINUTES),
            requested_ip=requested_ip,
        )
        self.db.add(token)
        self.db.commit()

        reset_url = f"{reset_url_base}{raw_token}"
        try:
            EmailService.send_password_reset_email(top_admin.email, top_admin.username, reset_url)
        except Exception:
            # Keep the public response identical even when the mail provider fails.
            logger.error("Password reset email could not be sent")

    # ------------------------------------------------------------------
    # Reset-Bestätigung
    # ------------------------------------------------------------------
    def confirm_reset(self, raw_token: str, new_password: str) -> User:
        """Validates the token (unexpired, unused) and sets the new password.

        Raises ValueError with a user-facing message on any failure.
        """
        try:
            token_hash = _hash_token(raw_token)
            candidate = self.db.query(PasswordResetToken).filter_by(token_hash=token_hash).first()
            if not candidate:
                raise ValueError("Der Reset-Link ist ungültig.")
            # Lock the account before tokens: parallel links for the same account serialize.
            user = self.db.query(User).filter_by(id=candidate.user_id).populate_existing().with_for_update().first()
            token = self.db.query(PasswordResetToken).filter_by(token_hash=token_hash).populate_existing().with_for_update().first()
            if not user or not user.is_active or user.role != UserRole.TOP_ADMIN:
                raise ValueError("Der Reset-Link ist ungültig.")
            if token.used_at is not None:
                raise ValueError("Dieser Reset-Link wurde bereits verwendet.")
            if token.expires_at <= datetime.utcnow():
                raise ValueError("Dieser Reset-Link ist abgelaufen. Bitte fordere einen neuen an.")
            token.used_at = datetime.utcnow()
            self.user_repo.update(user.id, password=new_password, failed_login_attempts=0, commit=False)
            # The shared User hook revokes all other links and earlier sessions in this transaction.
            self.audit.log(entity_type="auth", action="PASSWORD_RESET_COMPLETED",
                           user_username=user.username, entity_id=user.id, entity_name=user.username)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            raise
