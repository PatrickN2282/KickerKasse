from sqlalchemy.orm import Session
from app.models import CashEntry, CashBalance, CashEntryType
from sqlalchemy import desc, func
from datetime import date


class CashEntryRepository:
    """Repository for CashEntry model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        entry_type: CashEntryType,
        amount_cents: int,
        reason: str,
        user_id: int
    ) -> CashEntry:
        """Create new cash entry"""
        entry = CashEntry(
            entry_type=entry_type,
            amount_cents=amount_cents,
            reason=reason,
            user_id=user_id,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def get_by_id(self, entry_id: int) -> CashEntry:
        """Get entry by ID"""
        return self.db.query(CashEntry).filter(CashEntry.id == entry_id).first()
    
    def get_by_date(self, target_date: date) -> list:
        """Get all entries for a specific date"""
        return self.db.query(CashEntry).filter(
            func.date(CashEntry.created_at) == target_date
        ).order_by(CashEntry.created_at.desc()).all()
    
    def get_withdrawals(self, target_date: date = None) -> list:
        """Get all withdrawals, optionally filtered by date"""
        query = self.db.query(CashEntry).filter(
            CashEntry.entry_type == CashEntryType.WITHDRAWAL
        )
        
        if target_date:
            query = query.filter(func.date(CashEntry.created_at) == target_date)
        
        return query.order_by(CashEntry.created_at.desc()).all()
    
    def get_deposits(self, target_date: date = None) -> list:
        """Get all deposits, optionally filtered by date"""
        query = self.db.query(CashEntry).filter(
            CashEntry.entry_type == CashEntryType.DEPOSIT
        )
        
        if target_date:
            query = query.filter(func.date(CashEntry.created_at) == target_date)
        
        return query.order_by(CashEntry.created_at.desc()).all()
    
    def get_total_withdrawals(self, target_date: date = None) -> int:
        """Get total amount of withdrawals in cents"""
        query = self.db.query(func.sum(CashEntry.amount_cents)).filter(
            CashEntry.entry_type == CashEntryType.WITHDRAWAL
        )
        
        if target_date:
            query = query.filter(func.date(CashEntry.created_at) == target_date)
        
        result = query.scalar()
        return result or 0
    
    def get_total_deposits(self, target_date: date = None) -> int:
        """Get total amount of deposits in cents"""
        query = self.db.query(func.sum(CashEntry.amount_cents)).filter(
            CashEntry.entry_type == CashEntryType.DEPOSIT
        )
        
        if target_date:
            query = query.filter(func.date(CashEntry.created_at) == target_date)
        
        result = query.scalar()
        return result or 0


class CashBalanceRepository:
    """Repository for CashBalance model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        balance_date: date,
        opening_balance_cents: int = 0,
        closing_balance_cents: int = None,
        cash_sales_cents: int = 0,
        balance_recharges_cents: int = 0,
        cash_withdrawals_cents: int = 0,
        cash_deposits_cents: int = 0,
    ) -> CashBalance:
        """Create new cash balance record"""
        balance = CashBalance(
            balance_date=balance_date,
            opening_balance_cents=opening_balance_cents,
            closing_balance_cents=closing_balance_cents,
            cash_sales_cents=cash_sales_cents,
            balance_recharges_cents=balance_recharges_cents,
            cash_withdrawals_cents=cash_withdrawals_cents,
            cash_deposits_cents=cash_deposits_cents,
        )
        self.db.add(balance)
        self.db.commit()
        self.db.refresh(balance)
        return balance
    
    def get_by_id(self, balance_id: int) -> CashBalance:
        """Get balance by ID"""
        return self.db.query(CashBalance).filter(CashBalance.id == balance_id).first()
    
    def get_by_date(self, target_date: date) -> CashBalance:
        """Get balance for specific date"""
        return self.db.query(CashBalance).filter(
            func.date(CashBalance.balance_date) == target_date
        ).first()
    
    def get_latest(self) -> CashBalance:
        """Get latest cash balance"""
        return self.db.query(CashBalance).order_by(
            desc(CashBalance.balance_date)
        ).first()
    
    def get_all(self) -> list:
        """Get all cash balances, ordered latest first"""
        return self.db.query(CashBalance).order_by(
            desc(CashBalance.balance_date)
        ).all()
    
    def update(self, balance_id: int, **kwargs) -> CashBalance:
        """Update cash balance"""
        balance = self.get_by_id(balance_id)
        if not balance:
            return None
        
        for key, value in kwargs.items():
            if hasattr(balance, key):
                setattr(balance, key, value)
        
        self.db.commit()
        self.db.refresh(balance)
        return balance
    
    def delete(self, balance_id: int) -> bool:
        """Delete cash balance record"""
        balance = self.get_by_id(balance_id)
        if not balance:
            return False
        
        self.db.delete(balance)
        self.db.commit()
        return True
