from sqlalchemy import Column, String, Integer, DateTime, Float, Text
from sqlalchemy.sql import func
from .base import BaseModel


class ZBonHistory(BaseModel):
    """Track Z-Bon (Tagesabschluss) sequences and history"""
    __tablename__ = "zbon_history"

    sequence_number = Column(Integer, nullable=False, unique=True, index=True)  # Z-Bon Nummer (95, 96, ...)
    business_date = Column(DateTime, nullable=False, index=True)  # Geschäftstag
    generated_at = Column(DateTime, default=func.now(), nullable=False)  # Wann erstellt
    
    # Zeitraum der Z-Bon
    period_start = Column(DateTime, nullable=False)  # Von (letzte Z-Bon oder Tagesbeginn)
    period_end = Column(DateTime, nullable=False)  # Bis (jetzt)
    
    # Umsatzdaten (in EUR, gerundet)
    gross_revenue_cash = Column(Float, default=0.0, nullable=False)  # Bruttoumsatz BAR
    gross_revenue_balance = Column(Float, default=0.0, nullable=False)  # Bruttoumsatz GUTHABEN
    recharge_total = Column(Float, default=0.0, nullable=False)  # Guthabenaufladungen
    storno_total = Column(Float, default=0.0, nullable=False)  # Stornierungen
    
    # Kassenbestand
    cash_opening_balance = Column(Float, default=0.0, nullable=False)  # Kassenanfangsbestand
    cash_calculated = Column(Float, nullable=True)  # Kassenbestand berechnet
    cash_counted = Column(Float, nullable=True)  # Kassenbestand gezählt
    cash_difference = Column(Float, nullable=True)  # Differenz
    
    # Entnahmen/Einlagen an diesem Tag
    cash_withdrawals = Column(Float, default=0.0, nullable=False)  # Entnahmen
    cash_deposits = Column(Float, default=0.0, nullable=False)  # Einlagen
    
    # Transaktionszahlen
    transaction_count_sales = Column(Integer, default=0, nullable=False)
    transaction_count_recharge = Column(Integer, default=0, nullable=False)
    transaction_count_storno = Column(Integer, default=0, nullable=False)
    receipt_number_min = Column(Integer, nullable=True)  # Belegnr von
    receipt_number_max = Column(Integer, nullable=True)  # Belegnr bis
    
    # Report
    report_content = Column(Text, nullable=True)  # Der Z-Bon Text (für Archivierung)
    
    def __repr__(self):
        return f"<ZBonHistory #{self.sequence_number} - {self.business_date.strftime('%d.%m.%Y')}>"
