"""Service for Voucher operations"""
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from app.models import Voucher, VoucherType, VoucherStatus, VoucherReason, Transaction, TransactionType, PaymentMethod
from app.repositories.voucher_repository import VoucherRepository
import logging

logger = logging.getLogger(__name__)


class VoucherService:
    """Business logic for Vouchers"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = VoucherRepository(db)

    def create_gift_voucher(self, value_cents: int, reason: str, created_by_user_id: int, description: str = None) -> Voucher:
        """
        Create a GIFT voucher (ohne Zahlung)
        
        Args:
            value_cents: Value in cents
            reason: Reason (COURTESY, MARKETING, LOSS, OTHER)
            created_by_user_id: User who created this
            description: Optional description
            
        Returns:
            Created Voucher with number
        """
        # Validate reason
        try:
            reason_enum = VoucherReason(reason)
        except ValueError:
            raise ValueError(f"Invalid reason: {reason}")

        voucher = self.repository.create(
            voucher_type=VoucherType.GIFT,
            value_cents=value_cents,
            created_by_user_id=created_by_user_id,
            reason=reason_enum,
            description=description,
        )

        logger.info(f"Created GIFT voucher #{voucher.voucher_number}: {value_cents/100:.2f}€ ({reason})")
        return voucher

    def create_prepaid_voucher(self, value_cents: int, reason: str, created_by_user_id: int, description: str = None) -> Voucher:
        """
        Create a PREPAID voucher (wird später gekauft)
        
        Args:
            value_cents: Value in cents
            reason: Reason (COURTESY, PROMOTIONAL, STAFF_BENEFIT, OTHER)
            created_by_user_id: User who created this
            description: Optional description
            
        Returns:
            Created Voucher with number
        """
        # Validate reason
        try:
            reason_enum = VoucherReason(reason)
        except ValueError:
            raise ValueError(f"Invalid reason: {reason}")

        voucher = self.repository.create(
            voucher_type=VoucherType.PREPAID,
            value_cents=value_cents,
            created_by_user_id=created_by_user_id,
            reason=reason_enum,
            description=description,
        )

        logger.info(f"Created PREPAID voucher #{voucher.voucher_number}: {value_cents/100:.2f}€ ({reason})")
        return voucher

    def _format_voucher_identifier(self, voucher: Voucher) -> str:
        """Get display identifier for voucher"""
        if voucher.voucher_code:
            return voucher.voucher_code
        year = voucher.created_at.year if voucher.created_at else date.today().year
        return f"V-{year}-{str(voucher.voucher_number).zfill(3)}"

    def validate_voucher(self, voucher_number: str) -> dict:
        """
        Validate a voucher before redemption
        
        Args:
            voucher_number: Voucher number to validate
            
        Returns:
            Dict with voucher details and status
            
        Raises:
            ValueError if voucher not found or already redeemed
        """
        voucher = self.repository.get_by_number(voucher_number)
        
        if not voucher:
            return {
                "valid": False,
                "voucher_number": str(voucher_number),
                "voucher_type": "",
                "value_cents": 0,
                "status": "NOT_FOUND",
                "message": f"Voucher {voucher_number} not found",
                "reason": None,
            }

        if voucher.status == VoucherStatus.REDEEMED:
            redeemed_str = voucher.redeemed_at.strftime('%d.%m.%Y %H:%M') if voucher.redeemed_at else "unknown time"
            return {
                "valid": False,
                "voucher_number": self._format_voucher_identifier(voucher),
                "voucher_type": voucher.voucher_type.value,
                "value_cents": voucher.value_cents,
                "status": voucher.status.value,
                "message": f"Voucher already redeemed on {redeemed_str}",
                "reason": voucher.reason.value if voucher.reason else None,
            }

        return {
            "valid": True,
            "voucher_number": self._format_voucher_identifier(voucher),
            "voucher_type": voucher.voucher_type.value,
            "value_cents": voucher.value_cents,
            "status": voucher.status.value,
            "message": "Voucher is valid",
            "reason": voucher.reason.value if voucher.reason else None,
        }

    def redeem_gift_voucher(self, voucher_number: str, redeemed_by: int, member_id: Optional[int] = None) -> Transaction:
        """
        Redeem a GIFT voucher
        
        Creates a negative transaction (loss)
        
        Args:
            voucher_number: Voucher number
            user_id: User who redeems it
            
        Returns:
            Redeemed Voucher
        """
        voucher = self.repository.get_by_number(voucher_number)
        
        if not voucher:
            raise ValueError(f"Voucher #{voucher_number} not found")

        if voucher.voucher_type != VoucherType.GIFT:
            raise ValueError(f"Voucher #{voucher_number} is not a GIFT voucher")

        if voucher.status == VoucherStatus.REDEEMED:
            raise ValueError(f"Voucher #{voucher_number} already redeemed")

        # Create transaction for GIFT voucher (negative amount = loss)
        transaction = Transaction(
            type=TransactionType.VOUCHER_REDEMPTION,
            payment_method=PaymentMethod.VOUCHER_GIFT,
            total_amount_cents=-voucher.value_cents,  # Negative = loss
            user_id=redeemed_by,
            member_id=member_id,
        )
        self.db.add(transaction)
        self.db.flush()  # Get transaction ID without committing

        # Mark voucher as redeemed
        self.repository.redeem(voucher.id, redeemed_by, transaction.id)

        logger.info(f"Redeemed GIFT voucher #{voucher_number} ({voucher.value_cents/100:.2f}€) in transaction {transaction.id}")
        return transaction

    def redeem_prepaid_voucher(self, voucher_number: str, redeemed_by: int, member_id: Optional[int] = None) -> Transaction:
        """
        Redeem a PREPAID voucher
        
        Creates a null transaction (only payment method, no amount change)
        
        Args:
            voucher_number: Voucher number
            user_id: User who redeems it
            
        Returns:
            Redeemed Voucher
        """
        voucher = self.repository.get_by_number(voucher_number)
        
        if not voucher:
            raise ValueError(f"Voucher #{voucher_number} not found")

        if voucher.voucher_type != VoucherType.PREPAID:
            raise ValueError(f"Voucher #{voucher_number} is not a PREPAID voucher")

        if voucher.status == VoucherStatus.REDEEMED:
            raise ValueError(f"Voucher #{voucher_number} already redeemed")

        # Create transaction for PREPAID voucher (null amount = just payment method logging)
        transaction = Transaction(
            type=TransactionType.VOUCHER_REDEMPTION,
            payment_method=PaymentMethod.VOUCHER_PREPAID,
            total_amount_cents=0,  # Null transaction
            user_id=redeemed_by,
            member_id=member_id,
        )
        self.db.add(transaction)
        self.db.flush()

        # Mark voucher as redeemed
        self.repository.redeem(voucher.id, redeemed_by, transaction.id)

        logger.info(f"Redeemed PREPAID voucher #{voucher_number} in transaction {transaction.id}")
        return transaction

    def get_voucher_statistics(self, start_date: date, end_date: date) -> dict:
        """
        Get voucher statistics for a date range
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dict with statistics
        """
        gift_created = self.repository.count_by_type_and_status(VoucherType.GIFT, VoucherStatus.CREATED)
        gift_redeemed_count = self.repository.count_by_type_and_status(VoucherType.GIFT, VoucherStatus.REDEEMED)
        gift_redeemed_value = self.repository.sum_redeemed_by_type_and_date(VoucherType.GIFT, start_date, end_date)

        prepaid_created = self.repository.count_by_type_and_status(VoucherType.PREPAID, VoucherStatus.CREATED)
        prepaid_redeemed_count = self.repository.count_by_type_and_status(VoucherType.PREPAID, VoucherStatus.REDEEMED)
        prepaid_redeemed_value = self.repository.sum_redeemed_by_type_and_date(VoucherType.PREPAID, start_date, end_date)

        return {
            "gift": {
                "created": gift_created,
                "redeemed": gift_redeemed_count,
                "redeemed_value_cents": gift_redeemed_value,
                "redeemed_value_eur": gift_redeemed_value / 100.0,
            },
            "prepaid": {
                "created": prepaid_created,
                "redeemed": prepaid_redeemed_count,
                "redeemed_value_cents": prepaid_redeemed_value,
                "redeemed_value_eur": prepaid_redeemed_value / 100.0,
            },
        }
