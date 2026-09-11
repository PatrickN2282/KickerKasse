import json
import logging

from sqlalchemy.orm import Session

from app.models import AuditLog

logger = logging.getLogger(__name__)


SECRET_FIELDS = {"password", "password_hash", "auth_password", "account_password",
                 "smtp_password", "token", "reset_token", "secret_key", "authorization"}


def redact(value):
    if isinstance(value, dict):
        return {key: "[REDACTED]" if str(key).lower() in SECRET_FIELDS else redact(item)
                for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value


class AuditLogService:
    """Service for writing and reading admin audit log entries."""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        entity_type: str,
        action: str,
        user_username: str | None = None,
        entity_id: int | None = None,
        entity_name: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> AuditLog:
        """Write a single audit log entry."""
        entry = AuditLog(
            user_username=user_username,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            action=action,
            old_value=json.dumps(redact(old_value), default=str) if old_value is not None else None,
            new_value=json.dumps(redact(new_value), default=str) if new_value is not None else None,
        )
        self.db.add(entry)
        # Use flush so the entry participates in the surrounding transaction.
        # The caller is responsible for commit.
        self.db.flush()
        return entry

    def log_optional(self, **values) -> bool:
        """Operational events may fail, but the failure is visible in server logs."""
        try:
            with self.db.begin_nested():
                self.log(**values)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            logger.exception("Optional audit event failed: %s/%s",
                             values.get("entity_type"), values.get("action"))
            return False

    def get_all(self, skip: int = 0, limit: int = 200) -> list[AuditLog]:
        """Return audit log entries, newest first."""
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
