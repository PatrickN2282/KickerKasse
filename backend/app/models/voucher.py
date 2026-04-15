from sqlalchemy import Column, String, Integer, DateTime, Float, Text, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import BaseModel


class VoucherType(str, enum.Enum):
    """Voucher Types"""
    GIFT = "GIFT"          # Geschenk-Voucher (ohne Zahlung)
    PREPAID = "PREPAID"    # Prepaid-Voucher (mit Zahlung gekauft)


class VoucherStatus(str, enum.Enum):
    """Voucher Status"""
    CREATED = "CREATED"        # Erzeugt, noch nicht eingelöst
    REDEEMED = "REDEEMED"      # Eingelöst


class VoucherReason(str, enum.Enum):
    """Reason for GIFT vouchers (Grund für Geschenk-Gutschein)"""
    COURTESY = "COURTESY"          # Kulanz
    PROMOTIONAL = "PROMOTIONAL"    # Aktion/Werbung
    STAFF_BENEFIT = "STAFF_BENEFIT" # Mitarbeitervorteil
    OTHER = "OTHER"                # Sonstiges


class Voucher(BaseModel):
    """Voucher for gifts (GIFT) or prepaid (PREPAID)"""
    __tablename__ = "vouchers"

    voucher_number = Column(Integer, unique=True, nullable=False, index=True)  # Laufende Nummer (1, 2, 3...)
    voucher_code = Column(String(20), unique=True, nullable=False, index=True)  # Für Benutzer: V-2026-001, V-2026-002...
    voucher_type = Column(Enum(VoucherType), nullable=False, index=True)  # GIFT oder PREPAID
    status = Column(Enum(VoucherStatus), nullable=False, default=VoucherStatus.CREATED, index=True)
    
    # Value in cents
    value_cents = Column(Integer, nullable=False)  # Betrag in Cent
    
    # For GIFT vouchers: Reason
    reason = Column(Enum(VoucherReason), nullable=True)  # Grund (nur bei GIFT)
    
    description = Column(String(255), nullable=True)  # Optionale Beschreibung
    
    # Who created/redeemed this voucher
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    redeemed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Wer hat es eingelöst
    
    # When
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    redeemed_at = Column(DateTime, nullable=True)  # Wann eingelöst
    
    # Reference to transaction where voucher was redeemed
    redeemed_in_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    
    # Timestamps
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    redeemed_by_user = relationship("User", foreign_keys=[redeemed_by_user_id])
    redeemed_in_transaction = relationship("Transaction")

    def __repr__(self):
        return f"<Voucher #{self.voucher_number} {self.voucher_type} {self.value_cents/100:.2f}€ [{self.status}]>"
