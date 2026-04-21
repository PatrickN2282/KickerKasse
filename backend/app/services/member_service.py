from sqlalchemy.orm import Session
from app.repositories import MemberRepository, BalanceLogRepository


class MemberService:
    """Member management service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = MemberRepository(db)
        self.balance_log_repo = BalanceLogRepository(db)
    
    def create_member(
        self,
        first_name: str,
        last_name: str,
        membership_number: str = None,
        email: str = None,
        phone: str = None,
        notes: str = None,
        has_discount: bool = True,
        role: str | None = None,
    ):
        """Create a new member"""
        return self.repo.create(first_name, last_name, membership_number, email, phone, notes, has_discount, role)
    
    def get_member(self, member_id: int):
        """Get member by ID"""
        return self.repo.get_by_id(member_id)
    
    def get_all_members(self):
        """Get all members"""
        return self.repo.get_all()
    
    def update_member(self, member_id: int, **kwargs):
        """Update member"""
        return self.repo.update(member_id, **kwargs)
    
    def recharge_balance(self, member_id: int, amount_cents: int, reason: str = "RECHARGE"):
        """Recharge member balance"""
        member = self.repo.get_by_id(member_id)
        if not member:
            return None
        
        old_balance = member.balance_cents
        member = self.repo.add_balance(member_id, amount_cents)
        
        # Log balance change
        self.balance_log_repo.create(
            member_id=member_id,
            old_balance_cents=old_balance,
            new_balance_cents=member.balance_cents,
            reason=reason,
        )
        
        return member
    
    def check_sufficient_balance(self, member_id: int, amount_cents: int) -> bool:
        """Check if member has sufficient balance"""
        member = self.repo.get_by_id(member_id)
        return member and member.balance_cents >= amount_cents
    
    def delete_member(self, member_id: int):
        """Delete member"""
        return self.repo.delete(member_id)
