from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from datetime import date, datetime, time, timedelta
from app.repositories import TransactionRepository, BalanceLogRepository
from app.models import Transaction, TransactionType, PaymentMethod, Product, CashEntry, CashEntryType


class TransactionService:
    """Transaction service for sales and storni"""
    
    def __init__(self, db: Session):
        self.db = db
        self.transaction_repo = TransactionRepository(db)
        self.balance_log_repo = BalanceLogRepository(db)
    
    def get_next_receipt_number(self) -> int:
        """Gets the next sequential receipt number"""
        last_transaction = self.db.query(Transaction).order_by(Transaction.id.desc()).first()
        if last_transaction and last_transaction.receipt_number:
            return last_transaction.receipt_number + 1
        return 1

    def get_effective_price(self, product: Product, member_id: int = None) -> int:
        """Get the effective price for a product (member price if applicable)"""
        if member_id and product.member_price_cents:
            return product.member_price_cents
        return product.price_cents
    
    def create_sale_transaction(
        self,
        user_id: int,
        total_amount_cents: int,
        payment_method: str,
        member_id: int = None,
        items: list = None,
        voucher_code: str = None,
        voucher_type: str = None,
        voucher_applied_cents: int = 0,
        balance_applied_cents: int = 0,
    ) -> Transaction:
        """Create a sale transaction"""
        payment_enum = PaymentMethod[payment_method]
        
        transaction = self.transaction_repo.create(
            type=TransactionType.SALE,
            payment_method=payment_enum,
            total_amount_cents=total_amount_cents,
            user_id=user_id,
            member_id=member_id,
            items=items or [],
            voucher_code=voucher_code,
            voucher_type=voucher_type,
            voucher_applied_cents=voucher_applied_cents,
            balance_applied_cents=balance_applied_cents,
        )
        
        return transaction
    
    def process_sale_payment(self, transaction: Transaction, member_repo=None):
        """Process payment and update balances"""
        if transaction.member_id and transaction.balance_applied_cents > 0:
            if not member_repo:
                from app.repositories import MemberRepository
                member_repo = MemberRepository(self.db)
            
            # Deduct from member balance
            if not member_repo.deduct_balance(transaction.member_id, transaction.balance_applied_cents):
                raise ValueError("Insufficient balance")
            
            # Log balance change
            member = member_repo.get_by_id(transaction.member_id)
            self.balance_log_repo.create(
                member_id=transaction.member_id,
                old_balance_cents=member.balance_cents + transaction.balance_applied_cents,
                new_balance_cents=member.balance_cents,
                reason="SALE",
                transaction_id=transaction.id,
            )
    
    def create_storno_transaction(
        self,
        original_transaction_id: int,
        user_id: int,
    ) -> Transaction:
        """Create a storno (reversal) transaction"""
        original = self.transaction_repo.get_by_id(original_transaction_id)
        if not original:
            raise ValueError("Original transaction not found")
        
        # Create storno transaction with same amount
        storno = self.transaction_repo.create(
            type=TransactionType.STORNO,
            payment_method=original.payment_method,
            total_amount_cents=original.total_amount_cents,
            user_id=user_id,
            member_id=original.member_id,
            reference_transaction_id=original_transaction_id,
            voucher_code=original.voucher_code,
            voucher_type=original.voucher_type,
            voucher_applied_cents=original.voucher_applied_cents,
            balance_applied_cents=original.balance_applied_cents,
        )
        
        return storno
    
    def process_storno_payment(self, storno: Transaction, member_repo=None):
        """Process storno payment (reverse the original)"""
        if storno.member_id and storno.balance_applied_cents > 0:
            if not member_repo:
                from app.repositories import MemberRepository
                member_repo = MemberRepository(self.db)
            
            # Add balance back to member
            member_repo.add_balance(storno.member_id, storno.balance_applied_cents)
            
            # Log balance change
            member = member_repo.get_by_id(storno.member_id)
            self.balance_log_repo.create(
                member_id=storno.member_id,
                old_balance_cents=member.balance_cents - storno.balance_applied_cents,
                new_balance_cents=member.balance_cents,
                reason="STORNO",
                transaction_id=storno.id,
            )
    
    def get_daily_summary(self, date_from: date) -> dict:
        """Get Z-Bon (daily summary)"""
        transactions = self.transaction_repo.get_by_date(date_from)
        
        total_cash = 0
        total_balance = 0
        count = 0
        
        for transaction in transactions:
            if transaction.type == TransactionType.SALE:
                if transaction.payment_method == PaymentMethod.CASH:
                    total_cash += transaction.total_amount_cents
                total_balance += transaction.balance_applied_cents
                if transaction.payment_method == PaymentMethod.BALANCE:
                    total_balance += transaction.total_amount_cents
                count += 1
            elif transaction.type == TransactionType.VOUCHER_SALE and transaction.payment_method == PaymentMethod.CASH:
                total_cash += transaction.total_amount_cents
                count += 1
        
        return {
            "total_cash_cents": total_cash,
            "total_balance_cents": total_balance,
            "transaction_count": count,
            "date": date_from,
        }
    
    def get_transaction(self, transaction_id: int) -> Transaction | None:
        """Get transaction by ID"""
        return self.transaction_repo.get_by_id(transaction_id)
    
    def get_all_transactions(self, skip: int = 0, limit: int = 100) -> list[Transaction]:
        """Get all transactions"""
        return self.transaction_repo.get_all(skip=skip, limit=limit)
    
    def get_daily_stats(self, date_from: date):
        """Get detailed daily statistics with transaction list"""
        from datetime import datetime, time
        from app.models import TransactionItem
        
        # Create date range with proper timezone handling
        start_datetime = datetime.combine(date_from, time.min)
        end_datetime = datetime.combine(date_from, time.max)
        
        print(f"[Service] Fetching daily stats for {date_from} (range: {start_datetime} to {end_datetime})")
        
        transactions = self.db.query(Transaction).options(
            joinedload(Transaction.items).joinedload(TransactionItem.product)
        ).filter(
            Transaction.created_at >= start_datetime,
            Transaction.created_at <= end_datetime,
            Transaction.type.in_([
                TransactionType.SALE,
                TransactionType.RECHARGE,
                TransactionType.VOUCHER_REDEMPTION,
                TransactionType.VOUCHER_SALE,
            ])
        ).order_by(Transaction.created_at.desc()).all()
        
        print(f"[Service] Found {len(transactions)} transactions for {date_from}")
        
        total_cash = 0
        total_balance = 0
        total_voucher_gift = 0
        total_voucher_prepaid = 0
        total_prepaid_sales = 0
        count = 0
        
        for transaction in transactions:
            print(f"[Service] Transaction: id={transaction.id}, type={transaction.type}, payment={transaction.payment_method}, amount={transaction.total_amount_cents}, items={len(transaction.items)}")
            if transaction.payment_method == PaymentMethod.CASH:
                total_cash += transaction.total_amount_cents
            total_balance += transaction.balance_applied_cents
            if transaction.payment_method == PaymentMethod.BALANCE:
                total_balance += transaction.total_amount_cents

            if transaction.type == TransactionType.VOUCHER_SALE and transaction.voucher_type == "PREPAID":
                total_prepaid_sales += transaction.total_amount_cents

            if transaction.voucher_applied_cents:
                if transaction.voucher_type == "GIFT":
                    total_voucher_gift += transaction.voucher_applied_cents
                elif transaction.voucher_type == "PREPAID":
                    total_voucher_prepaid += transaction.voucher_applied_cents
            count += 1
        
        return {
            "cash_total": total_cash,
            "balance_total": total_balance,
            "voucher_gift_total": total_voucher_gift,
            "voucher_prepaid_total": total_voucher_prepaid,
            "voucher_total": total_voucher_gift + total_voucher_prepaid,
            "prepaid_voucher_sales_total": total_prepaid_sales,
            "total_amount": total_cash + total_balance,
            "transaction_count": count,
            "transactions": [
                {
                    "id": t.id,
                    "receipt_number": t.receipt_number,
                    "total_amount_cents": t.total_amount_cents,
                    "payment_method": t.payment_method.value,
                    "type": t.type.value,
                    "voucher_code": t.voucher_code,
                    "voucher_type": t.voucher_type,
                         "voucher_applied_cents": t.voucher_applied_cents,
                         "balance_applied_cents": t.balance_applied_cents,
                    "created_at": t.created_at,
                    "member": {
                        "id": t.member.id,
                        "name": t.member.name,
                    } if t.member else None,
                    "items": [
                        {
                            "id": item.id,
                            "quantity": item.quantity,
                            "unit_price_cents": item.unit_price_cents,
                            "total_price_cents": item.total_price_cents,
                            "is_internal_material": item.is_internal_material,
                            "product": {
                                "id": item.product.id,
                                "name": item.product.name,
                            }
                        }
                        for item in t.items
                    ]
                }
                for t in transactions
            ],
        }
    
    def get_filtered_transactions(self, start_date: date, end_date: date, payment_method: str = None):
        """Get filtered transactions with stats"""
        from datetime import datetime, time
        from app.models import TransactionItem
        
        # Create datetime range
        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(end_date, time.max)
        
        print(f"[Service] Filtering transactions from {start_datetime} to {end_datetime}")
        
        query = self.db.query(Transaction).options(
            joinedload(Transaction.items).joinedload(TransactionItem.product),
            joinedload(Transaction.user),
            joinedload(Transaction.member),
        ).filter(
            Transaction.created_at >= start_datetime,
            Transaction.created_at <= end_datetime,
            Transaction.type.in_([
                TransactionType.SALE,
                TransactionType.RECHARGE,
                TransactionType.VOUCHER_REDEMPTION,
                TransactionType.VOUCHER_SALE,
            ])
        )
        
        if payment_method:
            query = query.filter(Transaction.payment_method == PaymentMethod[payment_method])
        
        transactions = query.order_by(Transaction.created_at.desc(), Transaction.id.desc()).all()
        
        print(f"[Service] Found {len(transactions)} filtered transactions")
        
        total_amount = sum(t.total_amount_cents for t in transactions)
        
        return {
            "transactions": [
                {
                    "id": t.id,
                    "receipt_number": t.receipt_number,
                    "total_amount_cents": t.total_amount_cents,
                    "payment_method": t.payment_method.value,
                    "type": t.type.value,
                    "voucher_code": t.voucher_code,
                    "voucher_type": t.voucher_type,
                    "voucher_applied_cents": t.voucher_applied_cents,
                    "balance_applied_cents": t.balance_applied_cents,
                    "created_at": t.created_at,
                    "member": {
                        "id": t.member.id,
                        "name": t.member.name,
                    } if t.member else None,
                    "user": {
                        "id": t.user.id,
                        "username": t.user.username,
                    } if t.user else None,
                    "items": [
                        {
                            "id": item.id,
                            "quantity": item.quantity,
                            "unit_price_cents": item.unit_price_cents,
                            "total_price_cents": item.total_price_cents,
                            "is_internal_material": item.is_internal_material,
                            "product": {
                                "id": item.product.id,
                                "name": item.product.name,
                            } if item.product else None,
                        }
                        for item in t.items
                    ],
                }
                for t in transactions
            ],
            "total_amount": total_amount,
        }
    
    def get_revenue_stats(self):
        """Get revenue statistics"""
        from app.models import TransactionItem, Product
        
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Week stats
        week_transactions = self.db.query(Transaction).filter(
            func.date(Transaction.created_at) >= week_ago,
            func.date(Transaction.created_at) <= today,
            Transaction.type.in_([TransactionType.SALE, TransactionType.VOUCHER_SALE])
        ).all()
        
        week_total = sum(t.total_amount_cents for t in week_transactions)
        week_cash = sum(t.total_amount_cents for t in week_transactions if t.payment_method == PaymentMethod.CASH)
        week_balance = sum(t.total_amount_cents for t in week_transactions if t.payment_method == PaymentMethod.BALANCE)
        week_prepaid_sales = sum(
            t.total_amount_cents
            for t in week_transactions
            if t.type == TransactionType.VOUCHER_SALE and t.voucher_type == "PREPAID"
        )

        week_start = datetime.combine(week_ago, time.min)
        week_end = datetime.combine(today, time.max)
        week_withdrawals = (
            self.db.query(func.coalesce(func.sum(CashEntry.amount_cents), 0))
            .filter(
                CashEntry.entry_type == CashEntryType.WITHDRAWAL,
                CashEntry.created_at >= week_start,
                CashEntry.created_at <= week_end,
            )
            .scalar()
            or 0
        )
        
        # Month stats
        month_transactions = self.db.query(Transaction).filter(
            func.date(Transaction.created_at) >= month_ago,
            func.date(Transaction.created_at) <= today,
            Transaction.type.in_([TransactionType.SALE, TransactionType.VOUCHER_SALE])
        ).all()
        
        month_total = sum(t.total_amount_cents for t in month_transactions)
        month_prepaid_sales = sum(
            t.total_amount_cents
            for t in month_transactions
            if t.type == TransactionType.VOUCHER_SALE and t.voucher_type == "PREPAID"
        )
        month_start = datetime.combine(month_ago, time.min)
        month_end = datetime.combine(today, time.max)
        month_withdrawals = (
            self.db.query(func.coalesce(func.sum(CashEntry.amount_cents), 0))
            .filter(
                CashEntry.entry_type == CashEntryType.WITHDRAWAL,
                CashEntry.created_at >= month_start,
                CashEntry.created_at <= month_end,
            )
            .scalar()
            or 0
        )
        
        # Daily average
        daily_average = int(month_total / 30) if month_total > 0 else 0
        
        # Top products this week
        top_products = self.db.query(
            Product.id,
            Product.name,
            func.sum(TransactionItem.quantity).label('quantity_sold'),
            func.sum(TransactionItem.unit_price_cents * TransactionItem.quantity).label('total_revenue')
        ).join(TransactionItem).join(Transaction).filter(
            func.date(Transaction.created_at) >= week_ago,
            func.date(Transaction.created_at) <= today,
            Transaction.type == TransactionType.SALE
        ).group_by(Product.id, Product.name).order_by(
            func.sum(TransactionItem.unit_price_cents * TransactionItem.quantity).desc()
        ).limit(10).all()
        
        cash_percent = int((week_cash / week_total * 100)) if week_total > 0 else 0
        balance_percent = 100 - cash_percent
        
        return {
            "week_total": week_total,
            "month_total": month_total,
            "daily_average": daily_average,
            "cash_total": week_cash,
            "balance_total": week_balance,
            "prepaid_voucher_sales_total": week_prepaid_sales,
            "month_prepaid_voucher_sales_total": month_prepaid_sales,
            "week_withdrawals": int(week_withdrawals),
            "month_withdrawals": int(month_withdrawals),
            "cash_percent": cash_percent,
            "balance_percent": balance_percent,
            "top_products": [
                {
                    "id": p[0],
                    "name": p[1],
                    "quantity_sold": p[2] or 0,
                    "total_revenue": p[3] or 0,
                }
                for p in top_products
            ],
        }
