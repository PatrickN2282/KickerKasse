from sqlalchemy import Column, String, Integer, DateTime, Float, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import BaseModel


class CashEntryType(str, enum.Enum):
    WITHDRAWAL = "WITHDRAWAL"  # Entnahme
    DEPOSIT = "DEPOSIT"  # Einlage


class CashEntry(BaseModel):
    """Track cash deposits and withdrawals (Einlagen/Entnahmen)"""
    __tablename__ = "cash_entries"

    entry_type = Column(Enum(CashEntryType), nullable=False)  # Einlage oder Entnahme
    amount_cents = Column(Integer, nullable=False)  # Betrag in Cent
    reason = Column(String(255), nullable=False)  # Grund (z.B. "Abschöpfung Benny u.Carsten")
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Wer hat es gemacht
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<CashEntry {self.entry_type} {self.amount_cents/100:.2f}€>"


class CashBalance(BaseModel):
    """Daily cash balance snapshot"""
    __tablename__ = "cash_balances"

    balance_date = Column(DateTime, nullable=False, unique=True, index=True)  # Datum/Uhrzeit des Snapshots
    opening_balance_cents = Column(Integer, default=0, nullable=False)  # Kassenanfangsbestand
    closing_balance_cents = Column(Integer, nullable=True)  # Kassenabschlussbestand (gezählt)
    
    # Tagesumsätze
    cash_sales_cents = Column(Integer, default=0, nullable=False)  # Verkäufe BAR
    balance_recharges_cents = Column(Integer, default=0, nullable=False)  # Guthabenaufladungen
    cash_withdrawals_cents = Column(Integer, default=0, nullable=False)  # Entnahmen (Abschöpfungen)
    cash_deposits_cents = Column(Integer, default=0, nullable=False)  # Einlagen
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<CashBalance {self.balance_date.strftime('%d.%m.%Y')}>"
