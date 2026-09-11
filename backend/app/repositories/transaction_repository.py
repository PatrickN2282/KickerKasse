from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from app.models import Transaction, TransactionItem, TransactionType, PaymentMethod, BalanceLog, CashEntry, Product, Member, User
from datetime import datetime, date


class TransactionRepository:
    """Repository for Transaction model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        type: TransactionType,
        payment_method: PaymentMethod,
        total_amount_cents: int,
        user_id: int,
        member_id: int = None,
        member_name: str = None,
        performed_by_username: str = None,
        items: list = None,
        reference_transaction_id: int = None,
        voucher_code: str = None,
        voucher_type: str = None,
        voucher_applied_cents: int = 0,
        balance_applied_cents: int = 0,
        tip_cents: int = 0,
        cash_received_cents: int = None,
        change_given_cents: int = None,
        commit: bool = True,
    ) -> Transaction:
        """Create a new transaction"""
        actor = self.db.get(User, user_id)
        member_snapshot = self.db.get(Member, member_id) if member_id else None
        transaction = Transaction(
            type=type,
            booking_type=("MEMBER_BALANCE_RECHARGE" if member_id is not None else "CLUB_ACCOUNT_TOP_UP") if type == TransactionType.RECHARGE else getattr(type, "value", type),
            payment_method=payment_method,
            total_amount_cents=total_amount_cents,
            user_id=user_id,
            member_id=member_id,
            member_name=member_name or (member_snapshot.name if member_snapshot else None),
            performed_by_username=performed_by_username or (actor.username if actor else None),
            reference_transaction_id=reference_transaction_id,
            voucher_code=voucher_code,
            voucher_type=voucher_type,
            voucher_applied_cents=voucher_applied_cents or 0,
            balance_applied_cents=balance_applied_cents or 0,
            tip_cents=tip_cents or 0,
            cash_received_cents=cash_received_cents,
            change_given_cents=change_given_cents,
        )
        
        if items:
            for item_data in items:
                from app.services.sale_pricing_service import resolve_catalog_unit_price_cents
                product = self.db.get(Product, item_data["product_id"])
                member = self.db.get(Member, member_id) if member_id else None
                material = bool(item_data.get("is_internal_material", False))
                item = TransactionItem(
                    snapshot_version=1,
                    product_group_name=(product.warengruppe or "").strip() or "Ohne Warengruppe",
                    category_name=product.categories[0].name if product.categories else "Ohne Kategorie",
                    tax_rate_snapshot=product.tax_rate,
                    internal_material_unit_value_cents=resolve_catalog_unit_price_cents(product, member) if material else 0,
                    product_id=item_data["product_id"],
                    product_name=item_data.get("product_name") or product.name,
                    quantity=item_data["quantity"],
                    unit_price_cents=item_data["unit_price_cents"],
                    total_price_cents=item_data["quantity"] * item_data["unit_price_cents"],
                    is_internal_material=bool(item_data.get("is_internal_material", False)),
                    note=(item_data.get("note") or "").strip() or None,
                )
                transaction.items.append(item)
        
        transaction.receipt_number = self.get_next_receipt_number()
        self.db.add(transaction)
        self.db.flush()  # Flush to get the ID
         
        if commit:
            self.db.commit()
            self.db.refresh(transaction)
        return transaction

    def get_next_receipt_number(self) -> int:
        from app.core.financial_booking import next_receipt_number
        return next_receipt_number(self.db)
    
    def get_by_id(self, transaction_id: int) -> Transaction | None:
        """Get transaction by ID"""
        return self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    def get_all(self, product_id: int = None, skip: int = 0, limit: int = 100) -> list[Transaction]:
        """Get all transactions"""
        query = self.db.query(Transaction).order_by(desc(Transaction.created_at))
        if product_id:
            query = query.join(TransactionItem).filter(TransactionItem.product_id == product_id)
        return query.offset(skip).limit(limit).all()
    
    def get_by_member(self, member_id: int, skip: int = 0, limit: int = 100) -> list[Transaction]:
        """Get transactions by member"""
        return (
            self.db.query(Transaction)
            .filter(Transaction.member_id == member_id)
            .order_by(desc(Transaction.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_date(self, date_from: date, date_to: date = None) -> list[Transaction]:
        """Get transactions by date range"""
        query = self.db.query(Transaction)
        
        if date_to:
            query = query.filter(
                and_(
                    Transaction.created_at >= datetime.combine(date_from, datetime.min.time()),
                    Transaction.created_at <= datetime.combine(date_to, datetime.max.time()),
                )
            )
        else:
            query = query.filter(
                Transaction.created_at >= datetime.combine(date_from, datetime.min.time())
            )
        
        return query.order_by(desc(Transaction.created_at)).all()


class BalanceLogRepository:
    """Repository for BalanceLog model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        member_id: int,
        old_balance_cents: int,
        new_balance_cents: int,
        reason: str,
        transaction_id: int = None,
        commit: bool = True,
    ) -> BalanceLog:
        """Create a new balance log"""
        log = BalanceLog(
            member_id=member_id,
            transaction_id=transaction_id,
            old_balance_cents=old_balance_cents,
            new_balance_cents=new_balance_cents,
            change_cents=new_balance_cents - old_balance_cents,
            reason=reason,
        )
        self.db.add(log)
        if commit:
            self.db.commit()
            self.db.refresh(log)
        return log
    
    def get_by_member(self, member_id: int) -> list[BalanceLog]:
        """Get balance logs for a member"""
        return (
            self.db.query(BalanceLog)
            .filter(BalanceLog.member_id == member_id)
            .order_by(desc(BalanceLog.created_at))
            .all()
        )
