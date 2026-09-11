from sqlalchemy import Column, Float, Text, String, Integer, DateTime, Enum, ForeignKey, Boolean, Index, text
from sqlalchemy.orm import relationship, remote
from sqlalchemy.sql import func
import enum
from .base import BaseModel


class TransactionType(str, enum.Enum):
    SALE = "SALE"                      # Verkauf
    STORNO = "STORNO"                  # Storno (Rückgängigmachung)
    RECHARGE = "RECHARGE"              # Guthaben aufladen
    VOUCHER_CREATE = "VOUCHER_CREATE"  # Gutschein/Verzehrkarte erstellt
    VOUCHER_SALE = "VOUCHER_SALE"      # Voucher-Verkauf (Prepaid)
    VOUCHER_REDEMPTION = "VOUCHER_REDEMPTION"  # Voucher-Einlösung


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"                           # Bar
    BALANCE = "BALANCE"                     # Guthaben (Mitglieder)
    VOUCHER_GIFT = "VOUCHER_GIFT"           # Gutschein (Einlösung)
    VOUCHER_PREPAID = "VOUCHER_PREPAID"     # Prepaid-Voucher (Einlösung)


class Transaction(BaseModel):
    __tablename__ = "transactions"
    __table_args__ = (
        Index(
            "uq_transactions_storno_reference",
            "reference_transaction_id",
            unique=True,
            postgresql_where=text("type = 'STORNO'"),
        ),
    )

    zbon_history_id = Column(Integer, ForeignKey("zbon_history.id"), nullable=True, index=True)
    receipt_number = Column(Integer, unique=True, nullable=True, index=True)  # Laufende Belegnummer
    type = Column(Enum(TransactionType), nullable=False, default=TransactionType.SALE)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    total_amount_cents = Column(Integer, nullable=False)  # Gesamtbetrag in Cent
    voucher_code = Column(Text, nullable=True)
    voucher_type = Column(String(20), nullable=True)
    voucher_applied_cents = Column(Integer, nullable=False, default=0)
    balance_applied_cents = Column(Integer, nullable=False, default=0)
    tip_cents = Column(Integer, nullable=False, default=0)  # Trinkgeld-Spende
    cash_received_cents = Column(Integer, nullable=True)  # Tatsächlich entgegengenommenes Bargeld
    change_given_cents = Column(Integer, nullable=True)  # Tatsächlich ausgezahltes Rückgeld

    # Snapshot-Felder (unveränderlich nach Erstellung)
    booking_type = Column(String(40), nullable=True)
    member_name = Column(String(160), nullable=True)          # Name zum Kaufzeitpunkt
    performed_by_username = Column(String(50), nullable=True) # Benutzername des Kassierers

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
    voucher_redemptions = relationship("VoucherRedemption", back_populates="transaction")
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
    product_name = Column(String(120), nullable=True)  # Snapshot des Produktnamens zum Kaufzeitpunkt
    
    snapshot_version = Column(Integer, nullable=True)
    product_group_name = Column(String(120), nullable=True)
    category_name = Column(String(120), nullable=True)
    tax_rate_snapshot = Column(Float, nullable=True)
    internal_material_unit_value_cents = Column(Integer, nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price_cents = Column(Integer, nullable=False)  # Preis zum Zeitpunkt des Verkaufs
    total_price_cents = Column(Integer, nullable=False)  # quantity * unit_price
    is_internal_material = Column(Boolean, nullable=False, default=False)
    note = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    transaction = relationship("Transaction", back_populates="items")
    product = relationship("Product")

    def __repr__(self):
        return f"<TransactionItem {self.id}>"


class VoucherRedemption(BaseModel):
    __tablename__ = "voucher_redemptions"
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=False, index=True)
    voucher_code = Column(String(64), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    transaction = relationship("Transaction", back_populates="voucher_redemptions")
