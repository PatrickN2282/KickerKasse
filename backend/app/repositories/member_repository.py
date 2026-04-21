from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Member
from app.models.user import UserRole, parse_user_role

MAX_MEMBER_NUMBER_RETRIES = 3


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

    @staticmethod
    def _normalize_optional_string(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @staticmethod
    def _compose_name(first_name: str, last_name: str) -> str:
        return " ".join(part for part in [first_name.strip(), last_name.strip()] if part)

    @staticmethod
    def _normalize_role(role: str | UserRole | None) -> UserRole | None:
        return parse_user_role(role)

    @staticmethod
    def _is_member_number_conflict(error: IntegrityError) -> bool:
        constraint_name = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        if constraint_name:
            return "member_number" in constraint_name
        return "member_number" in str(error)

    def get_next_member_number(self) -> int:
        current_max = self.db.query(func.max(Member.member_number)).scalar()
        return (current_max or 0) + 1

    def create(
        self,
        first_name: str,
        last_name: str,
        membership_number: str = None,
        email: str = None,
        phone: str = None,
        notes: str = None,
        has_discount: bool = True,
        role: str | UserRole | None = None,
    ) -> Member:
        """Create a new member"""
        normalized_email = self._normalize_email(email)
        normalized_membership_number = self._normalize_optional_string(membership_number)
        normalized_role = self._normalize_role(role)
        last_exception = None

        for _ in range(MAX_MEMBER_NUMBER_RETRIES):
            member = Member(
                member_number=self.get_next_member_number(),
                name=self._compose_name(first_name, last_name),
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                membership_number=normalized_membership_number,
                email=normalized_email,
                phone=phone,
                notes=notes,
                has_discount=has_discount,
                role=normalized_role,
                balance_cents=0,
            )
            self.db.add(member)

            try:
                self.db.commit()
                self.db.refresh(member)
                return member
            except IntegrityError as exc:
                self.db.rollback()
                if not self._is_member_number_conflict(exc):
                    raise
                last_exception = exc

        raise last_exception
    
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
                elif key == "membership_number":
                    value = self._normalize_optional_string(value)
                elif key == "role":
                    value = self._normalize_role(value)
                setattr(member, key, value)

        if "first_name" in kwargs or "last_name" in kwargs:
            first_name = (member.first_name or "").strip()
            last_name = (member.last_name or "").strip()
            member.name = self._compose_name(first_name, last_name)

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
