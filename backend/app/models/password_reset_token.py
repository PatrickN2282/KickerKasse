from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class PasswordResetToken(BaseModel):
    """Self-Service-Passwort-Reset-Token für den TopAdmin-Account.

    Siehe Roadmap-UX-Sicherheit.md, Punkt 1 ("TOP-ADMIN PASSWORT-RESET-WORKFLOW"):
    Token sind zeitlich begrenzt (`expires_at`), nur einmal verwendbar und werden nach
    Nutzung sofort ungültig (`used_at` wird gesetzt). Es wird ausschließlich ein Hash des
    Tokens gespeichert (`token_hash`), niemals der Klartext-Wert - dieser wird nur per
    E-Mail an den Benutzer versendet.
    """

    __tablename__ = "password_reset_tokens"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    requested_ip = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User")

    def __repr__(self):
        return f"<PasswordResetToken user_id={self.user_id} used={self.used_at is not None}>"
