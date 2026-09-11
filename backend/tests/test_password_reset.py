"""Tests for the TopAdmin self-service password-reset workflow.

Covers Roadmap-UX-Sicherheit.md, Punkt 1:
  - Login-Fehlversuchszähler und Schwellenwert (5 Fehlversuche -> Reset-Dialog anbieten)
  - E-Mail-Abgleich (exakte Übereinstimmung erforderlich, sonst kein Token/keine Mail)
  - Token-Eigenschaften: zeitlich begrenzt, einmalig verwendbar, nach Nutzung sofort ungültig
"""
from datetime import datetime, timedelta

import pytest

from app.models import PasswordResetToken, UserRole
from app.repositories import UserRepository
from app.services.password_reset_service import (
    FAILED_LOGIN_THRESHOLD,
    PasswordResetService,
    _hash_token,
)


def _create_top_admin(db_session, *, email="admin@verein.de"):
    return UserRepository(db_session).create(
        username="topadmin",
        email=email,
        password="Initial12345!",
        role=UserRole.TOP_ADMIN.value,
    )


@pytest.fixture()
def stub_email(monkeypatch):
    """Replaces the real SMTP-backed email send with a recorder, since EmailService would
    otherwise try to open a real (PostgreSQL) DB session to load SMTP settings."""
    sent = []

    def _fake_send(recipient, username, reset_url):
        sent.append({"recipient": recipient, "username": username, "reset_url": reset_url})
        return True

    monkeypatch.setattr(
        "app.services.password_reset_service.EmailService.send_password_reset_email",
        staticmethod(_fake_send),
    )
    return sent


class TestFailedLoginCounter:
    def test_below_threshold_does_not_signal_reset(self, db_session):
        _create_top_admin(db_session)
        service = PasswordResetService(db_session)

        for _ in range(FAILED_LOGIN_THRESHOLD - 1):
            reset_available = service.register_failed_login("topadmin")
        assert reset_available is False

    def test_reaching_threshold_signals_reset(self, db_session):
        _create_top_admin(db_session)
        service = PasswordResetService(db_session)

        reset_available = False
        for _ in range(FAILED_LOGIN_THRESHOLD):
            reset_available = service.register_failed_login("topadmin")

        assert reset_available is True

    def test_non_top_admin_never_signals_reset(self, db_session):
        UserRepository(db_session).create(
            username="verkauf",
            email=None,
            password="Initial12345!",
            role=UserRole.VERKAUF.value,
        )
        service = PasswordResetService(db_session)

        for _ in range(FAILED_LOGIN_THRESHOLD + 5):
            reset_available = service.register_failed_login("verkauf")

        assert reset_available is False

    def test_unknown_username_does_not_error(self, db_session):
        service = PasswordResetService(db_session)
        assert service.register_failed_login("does-not-exist") is False

    def test_successful_login_resets_counter(self, db_session):
        user = _create_top_admin(db_session)
        service = PasswordResetService(db_session)
        for _ in range(FAILED_LOGIN_THRESHOLD):
            service.register_failed_login("topadmin")

        service.register_successful_login(user)
        db_session.refresh(user)
        assert user.failed_login_attempts == 0


class TestRequestReset:
    def test_matching_email_creates_single_use_token_and_sends_email(self, db_session, stub_email):
        _create_top_admin(db_session, email="admin@verein.de")
        service = PasswordResetService(db_session)

        service.request_reset(
            "admin@verein.de",
            reset_url_base="https://kasse.example.org/password-reset/",
            requested_ip="127.0.0.1",
        )

        tokens = db_session.query(PasswordResetToken).all()
        assert len(tokens) == 1
        assert tokens[0].used_at is None
        assert tokens[0].expires_at > datetime.utcnow()

        assert len(stub_email) == 1
        assert stub_email[0]["recipient"] == "admin@verein.de"
        assert stub_email[0]["reset_url"].startswith("https://kasse.example.org/password-reset/")

    def test_mismatching_email_does_not_create_token_or_send_email(self, db_session, stub_email):
        _create_top_admin(db_session, email="admin@verein.de")
        service = PasswordResetService(db_session)

        service.request_reset(
            "wrong@example.org",
            reset_url_base="https://kasse.example.org/password-reset/",
        )

        assert db_session.query(PasswordResetToken).count() == 0
        assert stub_email == []

    def test_request_reset_is_case_insensitive_on_email(self, db_session, stub_email):
        _create_top_admin(db_session, email="Admin@Verein.de")
        service = PasswordResetService(db_session)

        service.request_reset(
            "admin@verein.de",
            reset_url_base="https://kasse.example.org/password-reset/",
        )

        assert db_session.query(PasswordResetToken).count() == 1
        assert len(stub_email) == 1


class TestConfirmReset:
    def test_valid_token_sets_new_password_and_invalidates_token(self, db_session, stub_email):
        user = _create_top_admin(db_session, email="admin@verein.de")
        service = PasswordResetService(db_session)
        service.request_reset(
            "admin@verein.de",
            reset_url_base="https://kasse.example.org/password-reset/",
        )
        raw_token = stub_email[0]["reset_url"].rsplit("/", 1)[-1]

        updated_user = service.confirm_reset(raw_token, "BrandNewPassw0rd!")
        assert updated_user.id == user.id

        token = db_session.query(PasswordResetToken).first()
        assert token.used_at is not None

        from app.core.security import get_password_hasher
        hasher = get_password_hasher()
        db_session.refresh(user)
        assert hasher.verify_password("BrandNewPassw0rd!", user.password_hash)

    def test_token_cannot_be_reused(self, db_session, stub_email):
        _create_top_admin(db_session, email="admin@verein.de")
        service = PasswordResetService(db_session)
        service.request_reset(
            "admin@verein.de",
            reset_url_base="https://kasse.example.org/password-reset/",
        )
        raw_token = stub_email[0]["reset_url"].rsplit("/", 1)[-1]

        service.confirm_reset(raw_token, "FirstPassw0rd!")

        with pytest.raises(ValueError, match="bereits verwendet"):
            service.confirm_reset(raw_token, "SecondPassw0rd!")

    def test_expired_token_is_rejected(self, db_session):
        user = _create_top_admin(db_session, email="admin@verein.de")
        expired_token = PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_token("expired-raw-token"),
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        db_session.add(expired_token)
        db_session.commit()

        service = PasswordResetService(db_session)
        with pytest.raises(ValueError, match="abgelaufen"):
            service.confirm_reset("expired-raw-token", "NewPassw0rd!")

    def test_unknown_token_is_rejected(self, db_session):
        service = PasswordResetService(db_session)
        with pytest.raises(ValueError, match="ungültig"):
            service.confirm_reset("not-a-real-token", "NewPassw0rd!")
