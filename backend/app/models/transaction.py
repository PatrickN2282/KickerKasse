from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship, remote
from sqlalchemy.sql import func
import enum
from .base import BaseModel


class TransactionType(str, enum.Enum):
    SALE = "SALE"  # Verkauf
    STORNO = "STORNO"  # Storno (Rückgängigmachung)
    RECHARGE = "RECHARGE"  # Guthaben aufladen


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"  # Bar
    BALANCE = "BALANCE"  # Guthaben (Mitglieder)


class Transaction(BaseModel):
    __tablename__ = "transactions"

    receipt_number = Column(Integer, unique=True, nullable=True, index=True)  # Laufende Belegnummer
    type = Column(Enum(TransactionType), nullable=False, default=TransactionType.SALE)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    total_amount_cents = Column(Integer, nullable=False)  # Gesamtbetrag in Cent
    
    # Referenzen
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Kassierer/Admin
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)  # Kunde (wenn Mitglied)
    
    # Für Storno
    reference_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    items = relationship("TransactionItem", back_populates="transaction")
    user = relationship("User")
    member = relationship("Member")
    reference_transaction = relationship(
        "Transaction",
        remote_side="Transaction.id"
    )

    def __repr__(self):
        return f"<Transaction {self.id} - {self.type}>"


class TransactionItem(BaseModel):
    __tablename__ = "transaction_items"

    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    unit_price_cents = Column(Integer, nullable=False)  # Preis zum Zeitpunkt des Verkaufs
    total_price_cents = Column(Integer, nullable=False)  # quantity * unit_price
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    transaction = relationship("Transaction", back_populates="items")
    product = relationship("Product")

    def __repr__(self):
        return f"<TransactionItem {self.id}>"
