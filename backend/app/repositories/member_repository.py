from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Member


class MemberRepository:
    """Repository for Member model"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def _normalize_email(email: str | None) -> str | None:
        if email is None:
            return None
        email = email.strip()
        return email or None

    def get_next_member_number(self) -> int:
        current_max = self.db.query(
            func.max(func.coalesce(Member.member_number, Member.id))
        ).scalar()
        return (current_max or 0) + 1

    def create(self, name: str, email: str = None, phone: str = None, notes: str = None) -> Member:
        """Create a new member"""
        member = Member(
            member_number=self.get_next_member_number(),
            name=name,
            email=self._normalize_email(email),
            phone=phone,
            notes=notes,
            balance_cents=0,
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def get_by_id(self, member_id: int) -> Member | None:
        """Get member by ID"""
        return self.db.query(Member).filter(Member.id == member_id).first()
    
    def get_all(self) -> list[Member]:
        """Get all members"""
        return self.db.query(Member).order_by(Member.member_number, Member.name).all()
    
    def update(self, member_id: int, **kwargs) -> Member | None:
        """Update member"""
        member = self.get_by_id(member_id)
        if not member:
            return None
        
        for key, value in kwargs.items():
            if hasattr(member, key) and key != "id":
                if key == "email":
                    value = self._normalize_email(value)
                setattr(member, key, value)
        
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def add_balance(self, member_id: int, amount_cents: int) -> Member | None:
        """Add balance to member"""
        member = self.get_by_id(member_id)
        if not member:
            return None
        
        member.balance_cents += amount_cents
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def deduct_balance(self, member_id: int, amount_cents: int) -> bool:
        """Deduct balance from member. Returns False if insufficient balance"""
        member = self.get_by_id(member_id)
        if not member:
            return False
        
        if member.balance_cents < amount_cents:
            return False
        
        member.balance_cents -= amount_cents
        self.db.commit()
        return True
    
    def delete(self, member_id: int) -> bool:
        """Delete member"""
        member = self.get_by_id(member_id)
        if not member:
            return False
        
        self.db.delete(member)
        self.db.commit()
        return True
