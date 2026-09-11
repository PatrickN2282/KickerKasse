from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    id: int
    username: str
    email: str | None
    role: str
    message: str = "Login successful"
    # Anforderung 1: Nach 5 aufeinanderfolgenden Fehlversuchen des TopAdmin-Logins muss das
    # Frontend automatisch den Self-Service-Passwort-Reset-Dialog öffnen können.
    top_admin_reset_available: bool = False


class SetupStatusResponse(BaseModel):
    setup_required: bool
    top_admin_exists: bool
    top_admin_reset_email_channel_configured: bool = False


class TopAdminSetupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    # Anforderung 1: Beim allerersten Start muss zwingend eine E-Mail-Adresse für den
    # TopAdmin hinterlegt werden, damit ein Self-Service-Passwort-Reset später möglich ist.
    # Ohne hinterlegte E-Mail darf die Ersteinrichtung nicht abgeschlossen werden.
    email: str = Field(..., min_length=3, max_length=120)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = (value or "").strip()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Bitte eine gültige E-Mail-Adresse angeben")
        return normalized


class PasswordResetRequestRequest(BaseModel):
    """Schritt 1 des TopAdmin-Self-Service-Resets: hinterlegte E-Mail bestätigen."""
    email: str = Field(..., min_length=3, max_length=120)


class PasswordResetConfirmRequest(BaseModel):
    """Schritt 2: neues Passwort mit dem per E-Mail erhaltenen Token setzen."""
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8)
