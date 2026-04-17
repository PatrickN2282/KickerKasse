"""Repository for Voucher operations"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, text
from datetime import datetime, date
from app.models import Voucher, VoucherType, VoucherStatus
import logging

logger = logging.getLogger(__name__)


class VoucherRepository:
    """Handle Voucher database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        voucher_type: VoucherType,
        value_cents: int,
        created_by_user_id: int,
        reason: str = None,
        description: str = None,
    ) -> Voucher:
        """Create a new voucher and generate next number"""
        # Get next sequence number
        last_voucher = self.db.query(Voucher).order_by(desc(Voucher.voucher_number)).first()
        next_number = (last_voucher.voucher_number + 1) if last_voucher else 1

        # Generate voucher code: V-JAHR-NUMMER (e.g., V-2026-001)
        year = datetime.now().year
        voucher_code = f"V-{year}-{next_number:03d}"

        voucher = Voucher(
            voucher_number=next_number,
            voucher_code=voucher_code,
            voucher_type=voucher_type,
            value_cents=value_cents,
            created_by_user_id=created_by_user_id,
            reason=reason,
            description=description,
            status=VoucherStatus.CREATED,
        )
        
        logger.debug(f"[DEBUG] Before add: voucher_code={voucher.voucher_code}, type={type(voucher.voucher_code)}")
        
        try:
            self.db.add(voucher)
            logger.debug(f"[DEBUG] After add (before flush): voucher_code={voucher.voucher_code}, id={getattr(voucher, 'id', 'NOT SET')}")
            
            self.db.flush()  # Force flush to catch errors early
            logger.debug(f"[DEBUG] After flush: voucher_code={voucher.voucher_code}, id={voucher.id}")
            
            self.db.commit()
            logger.debug(f"[DEBUG] After commit: voucher_code={voucher.voucher_code}")
            
            self.db.refresh(voucher)
            logger.debug(f"[DEBUG] After refresh: voucher_code={voucher.voucher_code}, status={voucher.status}")
            
            # CRITICAL CHECK: Ensure voucher_code is set before returning
            if not voucher.voucher_code:
                logger.error(f"[CRITICAL] voucher_code is NULL after create! ID={voucher.id}")
                logger.info(f"Setting voucher_code manually to {voucher_code}...")
                
                # Update the database directly to ensure it's set
                self.db.execute(text("UPDATE vouchers SET voucher_code = :code WHERE id = :id"), 
                               {"code": voucher_code, "id": voucher.id})
                self.db.commit()
                self.db.refresh(voucher)
                
                logger.info(f"After manual update: voucher_code={voucher.voucher_code}")
            
            logger.info(f"Created {voucher_type} voucher {voucher.voucher_code} (#{voucher.voucher_number}, ID:{voucher.id}) for {value_cents/100:.2f}€")
            return voucher
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"[ERROR] Error creating voucher: {str(e)}", exc_info=True)
            raise

    def get_by_id(self, voucher_id: int) -> Voucher:
        """Get voucher by ID"""
        return self.db.query(Voucher).filter(Voucher.id == voucher_id).first()

    def get_by_number(self, voucher_number) -> Voucher:
        """Get voucher by number or code (handles both V-2026-001 and numeric formats)"""
        if isinstance(voucher_number, str) and voucher_number.startswith('V-'):
            # It's a voucher code
            return self.db.query(Voucher).filter(Voucher.voucher_code == voucher_number).first()
        else:
            # Try as numeric
            try:
                num = int(voucher_number)
                return self.db.query(Voucher).filter(Voucher.voucher_number == num).first()
            except (ValueError, TypeError):
                return None

    def get_all(self, limit: int = 100, offset: int = 0) -> tuple:
        """Get all vouchers, returns (vouchers, total)"""
        query = self.db.query(Voucher)
        total = query.count()
        vouchers = query.order_by(desc(Voucher.voucher_number)).limit(limit).offset(offset).all()
        return vouchers, total

    def get_all_by_status(self, status: VoucherStatus, skip: int = 0, limit: int = 100) -> tuple:
        """Get all vouchers by status, returns (vouchers, total)"""
        query = self.db.query(Voucher).filter(Voucher.status == status)
        total = query.count()
        vouchers = query.order_by(desc(Voucher.voucher_number)).offset(skip).limit(limit).all()
        return vouchers, total

    def get_all_by_type(self, voucher_type: VoucherType, skip: int = 0, limit: int = 100) -> tuple:
        """Get all vouchers by type, returns (vouchers, total)"""
        query = self.db.query(Voucher).filter(Voucher.voucher_type == voucher_type)
        total = query.count()
        vouchers = query.order_by(desc(Voucher.voucher_number)).offset(skip).limit(limit).all()
        return vouchers, total

    def get_all_by_type_and_status(
        self, voucher_type: VoucherType, status: VoucherStatus, skip: int = 0, limit: int = 100
    ) -> tuple:
        """Get vouchers by type and status, returns (vouchers, total)"""
        query = self.db.query(Voucher).filter(Voucher.voucher_type == voucher_type, Voucher.status == status)
        total = query.count()
        vouchers = query.order_by(desc(Voucher.voucher_number)).offset(skip).limit(limit).all()
        return vouchers, total

    def get_all_by_date_range(self, start_date: date, end_date: date, limit: int = 100, offset: int = 0) -> list:
        """Get vouchers by date range"""
        return (
            self.db.query(Voucher)
            .filter(
                Voucher.created_at >= datetime.combine(start_date, datetime.min.time()),
                Voucher.created_at <= datetime.combine(end_date, datetime.max.time()),
            )
            .order_by(desc(Voucher.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def redeem(
        self,
        voucher_id: int,
        redeemed_by_user_id: int,
        transaction_id: int,
        applied_amount_cents: int = None,
        commit: bool = True,
    ) -> Voucher:
        """Mark voucher as redeemed"""
        voucher = self.get_by_id(voucher_id)
        if not voucher:
            raise ValueError(f"Voucher {voucher_id} not found")

        if voucher.status == VoucherStatus.REDEEMED:
            raise ValueError(f"Voucher {voucher.voucher_number} already redeemed")

        voucher.status = VoucherStatus.REDEEMED
        voucher.redeemed_by_user_id = redeemed_by_user_id
        voucher.redeemed_at = datetime.now()
        voucher.redeemed_in_transaction_id = transaction_id
        voucher.redeemed_amount_cents = applied_amount_cents if applied_amount_cents is not None else voucher.value_cents

        if commit:
            self.db.commit()
            self.db.refresh(voucher)
        else:
            self.db.flush()
        
        logger.info(f"Redeemed voucher #{voucher.voucher_number} in transaction {transaction_id}")
        return voucher

    def update(self, voucher_id: int, commit: bool = True, **kwargs) -> Voucher:
        """Update editable voucher fields"""
        voucher = self.get_by_id(voucher_id)
        if not voucher:
            raise ValueError(f"Voucher {voucher_id} not found")

        for key, value in kwargs.items():
            if hasattr(voucher, key):
                setattr(voucher, key, value)

        if commit:
            self.db.commit()
            self.db.refresh(voucher)
        else:
            self.db.flush()
        return voucher

    def count_by_status(self, status: VoucherStatus) -> int:
        """Count vouchers by status"""
        return self.db.query(Voucher).filter(Voucher.status == status).count()

    def count_by_type_and_status(self, voucher_type: VoucherType, status: VoucherStatus) -> int:
        """Count vouchers by type and status"""
        return self.db.query(Voucher).filter(
            Voucher.voucher_type == voucher_type,
            Voucher.status == status,
        ).count()

    def sum_redeemed_by_type_and_date(self, voucher_type: VoucherType, start_date: date, end_date: date) -> int:
        """Sum value of redeemed vouchers by type and date (in cents)"""
        result = self.db.query(func.sum(Voucher.value_cents)).filter(
            Voucher.voucher_type == voucher_type,
            Voucher.status == VoucherStatus.REDEEMED,
            Voucher.redeemed_at >= datetime.combine(start_date, datetime.min.time()),
            Voucher.redeemed_at <= datetime.combine(end_date, datetime.max.time()),
        ).scalar()
        return result or 0
