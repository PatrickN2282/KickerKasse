"""Tests for auth-related request schemas.

Covers Roadmap-UX-Sicherheit.md, Punkt 1: the initial TopAdmin setup must not be completable
without a valid, non-empty email address (required for the later self-service reset flow).
"""
import pytest
from pydantic import ValidationError

from app.schemas.auth import TopAdminSetupRequest


class TestTopAdminSetupRequestEmail:
    def test_valid_email_is_accepted(self):
        request = TopAdminSetupRequest(username="topadmin", password="Initial123!", email="admin@verein.de")
        assert request.email == "admin@verein.de"

    def test_missing_email_is_rejected(self):
        with pytest.raises(ValidationError):
            TopAdminSetupRequest(username="topadmin", password="Initial123!")

    def test_empty_email_is_rejected(self):
        with pytest.raises(ValidationError):
            TopAdminSetupRequest(username="topadmin", password="Initial123!", email="")

    def test_email_without_at_sign_is_rejected(self):
        with pytest.raises(ValidationError):
            TopAdminSetupRequest(username="topadmin", password="Initial123!", email="not-an-email")

    def test_email_is_trimmed(self):
        request = TopAdminSetupRequest(username="topadmin", password="Initial123!", email="  admin@verein.de  ")
        assert request.email == "admin@verein.de"
