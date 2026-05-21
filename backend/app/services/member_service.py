from sqlalchemy.orm import Session

from app.models import (
    BalanceLog,
    CashEntry,
    ClubAccountEntry,
    Deckel,
    MemberBalanceCorrectionLog,
    MaterialAccountEntry,
    Member,
    Transaction,
    Voucher,
)
from app.repositories import MemberRepository, BalanceLogRepository, UserRepository
from app.services.file_service import delete_member_photo


class MemberService:
    """Member management service"""
    MAX_USERNAME_COLLISION_RETRIES = 100
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = MemberRepository(db)
        self.balance_log_repo = BalanceLogRepository(db)
        self.user_repo = UserRepository(db)

    def _audit(self, action: str, member: Member, user_username: str | None, old_value: dict | None = None, new_value: dict | None = None):
        """Write an audit log entry for a member action."""
        try:
            from app.services.audit_log_service import AuditLogService
            AuditLogService(self.db).log(
                entity_type="member",
                action=action,
                user_username=user_username,
                entity_id=member.id,
                entity_name=member.name,
                old_value=old_value,
                new_value=new_value,
            )
        except Exception:
            pass  # Audit failures must never break the main operation

    def _generate_member_username(self, member: Member) -> str:
        first_name = ".".join((member.first_name or "").split()).strip(".")
        last_name = ".".join((member.last_name or "").split()).strip(".")
        base = ".".join(part for part in [first_name, last_name] if part) or "Mitglied"
        candidate = base

        for suffix_index in range(self.MAX_USERNAME_COLLISION_RETRIES):
            existing_user = self.user_repo.get_by_username(candidate)
            if not existing_user or existing_user.member_id == member.id:
                return candidate
            candidate = f"{base}.{suffix_index + 2}"

        raise ValueError("Es konnte kein eindeutiger Benutzername generiert werden")

    def _validate_linked_user_state(
        self,
        *,
        email: str | None,
        role,
        linked_user,
        account_password: str | None,
    ) -> None:
        normalized_role = getattr(role, "value", role)
        if normalized_role == "TOP_ADMIN":
            raise ValueError("Top-Admin kann nicht an Mitglieder vergeben werden")

        if normalized_role and not linked_user and not account_password:
            raise ValueError("Mitglieder mit Rolle benötigen ein Passwort für den Benutzerzugang")

        if email:
            existing_user = self.user_repo.get_by_email(email)
            if existing_user and (not linked_user or existing_user.id != linked_user.id):
                raise ValueError("Diese E-Mail-Adresse existiert bereits")

    def _sync_linked_user(self, member: Member, account_password: str | None = None) -> None:
        linked_user = self.user_repo.get_by_member_id(member.id)

        if member.role:
            if linked_user:
                update_data = {
                    "email": member.email,
                    "role": member.role,
                    "is_active": True,
                    "member_id": member.id,
                }
                if account_password:
                    update_data["password"] = account_password
                self.user_repo.update(linked_user.id, **update_data)
                return

            self.user_repo.create(
                username=self._generate_member_username(member),
                email=member.email,
                password=account_password,
                role=member.role,
                member_id=member.id,
                is_active=True,
            )
            return

        if linked_user:
            self.user_repo.update(
                linked_user.id,
                email=member.email,
                is_active=False,
                member_id=member.id,
            )
    
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
        account_password: str | None = None,
        performed_by_username: str | None = None,
    ):
        """Create a new member"""
        self._validate_linked_user_state(
            email=email,
            role=role,
            linked_user=None,
            account_password=account_password,
        )
        member = self.repo.create(first_name, last_name, membership_number, email, phone, notes, has_discount, role)
        try:
            self._sync_linked_user(member, account_password)
            self.db.refresh(member)
            self._audit(
                "CREATED",
                member,
                performed_by_username,
                new_value={
                    "first_name": first_name,
                    "last_name": last_name,
                    "membership_number": membership_number,
                    "email": email,
                    "has_discount": has_discount,
                },
            )
            self.db.commit()
            self.db.refresh(member)
            return member
        except Exception:
            self.db.rollback()
            if self.repo.get_by_id(member.id):
                self.repo.delete(member.id)
            raise
    
    def get_member(self, member_id: int):
        """Get member by ID"""
        return self.repo.get_by_id(member_id)
    
    def get_all_members(self):
        """Get all members"""
        return self.repo.get_all()
    
    def update_member(self, member_id: int, account_password: str | None = None, performed_by_username: str | None = None, **kwargs):
        """Update member"""
        existing_member = self.repo.get_by_id(member_id)
        if not existing_member:
            return None

        old_snapshot = {
            "name": existing_member.name,
            "email": existing_member.email,
            "membership_number": existing_member.membership_number,
            "has_discount": existing_member.has_discount,
            "notes": existing_member.notes,
        }

        linked_user = self.user_repo.get_by_member_id(member_id)
        self._validate_linked_user_state(
            email=kwargs.get("email", existing_member.email),
            role=kwargs.get("role", existing_member.role),
            linked_user=linked_user,
            account_password=account_password,
        )

        member = self.repo.update(member_id, **kwargs)
        if not member:
            return None

        self._sync_linked_user(member, account_password)
        self.db.refresh(member)
        self._audit("UPDATED", member, performed_by_username, old_value=old_snapshot, new_value=kwargs)
        self.db.commit()
        self.db.refresh(member)
        return member
    
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

    def correct_balance(
        self,
        member_id: int,
        new_balance_cents: int,
        executed_by_username: str,
        reason: str | None = None,
    ):
        """Set member balance without cash flow and create a separate correction audit log."""
        member = self.repo.get_by_id(member_id)
        if not member:
            return None

        old_balance = member.balance_cents
        member.balance_cents = new_balance_cents
        correction_reason = (reason or "").strip() or "KORREKTURBUCHUNG"

        log = MemberBalanceCorrectionLog(
            member_id=member.id,
            member_name=member.name,
            old_balance_cents=old_balance,
            new_balance_cents=new_balance_cents,
            change_cents=new_balance_cents - old_balance,
            executed_by_username=executed_by_username,
            reason=correction_reason,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(member)
        self.db.refresh(log)
        return member

    def get_balance_correction_logs(self):
        """Get all member balance correction logs."""
        return (
            self.db.query(MemberBalanceCorrectionLog)
            .order_by(MemberBalanceCorrectionLog.created_at.desc(), MemberBalanceCorrectionLog.id.desc())
            .all()
        )
    
    def check_sufficient_balance(self, member_id: int, amount_cents: int) -> bool:
        """Check if member has sufficient balance"""
        member = self.repo.get_by_id(member_id)
        return member and member.balance_cents >= amount_cents
    
    def delete_member(self, member_id: int, performed_by_username: str | None = None):
        """Delete member"""
        member = self.repo.get_by_id(member_id)
        if not member:
            return False

        member_snapshot = {"name": member.name, "email": member.email}
        linked_user = self.user_repo.get_by_member_id(member_id)

        # Keep historical transaction amounts, timestamps, and receipt metadata for statistics/audits while
        # removing only the deleted member foreign key reference.
        self.db.query(Transaction).filter(Transaction.member_id == member_id).update(
            {Transaction.member_id: None},
            synchronize_session=False,
        )
        self.db.query(BalanceLog).filter(BalanceLog.member_id == member_id).delete(synchronize_session=False)

        if linked_user:
            has_user_references = any([
                self.db.query(Transaction.id).filter(Transaction.user_id == linked_user.id).first(),
                self.db.query(CashEntry.id).filter(CashEntry.user_id == linked_user.id).first(),
                self.db.query(ClubAccountEntry.id).filter(ClubAccountEntry.user_id == linked_user.id).first(),
                self.db.query(MaterialAccountEntry.id).filter(MaterialAccountEntry.user_id == linked_user.id).first(),
                self.db.query(Deckel.id).filter(Deckel.created_by_user_id == linked_user.id).first(),
                self.db.query(Voucher.id).filter(Voucher.created_by_user_id == linked_user.id).first(),
                self.db.query(Voucher.id).filter(Voucher.redeemed_by_user_id == linked_user.id).first(),
            ])

            if has_user_references:
                self.user_repo.update(
                    linked_user.id,
                    is_active=False,
                    member_id=None,
                    email=None,
                )
            else:
                self.user_repo.delete(linked_user.id)

        delete_member_photo(member_id)
        result = self.repo.delete(member_id)
        if result:
            try:
                from app.services.audit_log_service import AuditLogService
                AuditLogService(self.db).log(
                    entity_type="member",
                    action="DELETED",
                    user_username=performed_by_username,
                    entity_id=member_id,
                    entity_name=member_snapshot["name"],
                    old_value=member_snapshot,
                )
                self.db.commit()
            except Exception:
                pass
        return result


    def _generate_member_username(self, member: Member) -> str:
        first_name = ".".join((member.first_name or "").split()).strip(".")
        last_name = ".".join((member.last_name or "").split()).strip(".")
        base = ".".join(part for part in [first_name, last_name] if part) or "Mitglied"
        candidate = base

        for suffix_index in range(self.MAX_USERNAME_COLLISION_RETRIES):
            existing_user = self.user_repo.get_by_username(candidate)
            if not existing_user or existing_user.member_id == member.id:
                return candidate
            candidate = f"{base}.{suffix_index + 2}"

        raise ValueError("Es konnte kein eindeutiger Benutzername generiert werden")

    def _validate_linked_user_state(
        self,
        *,
        email: str | None,
        role,
        linked_user,
        account_password: str | None,
    ) -> None:
        normalized_role = getattr(role, "value", role)
        if normalized_role == "TOP_ADMIN":
            raise ValueError("Top-Admin kann nicht an Mitglieder vergeben werden")

        if normalized_role and not linked_user and not account_password:
            raise ValueError("Mitglieder mit Rolle benötigen ein Passwort für den Benutzerzugang")

        if email:
            existing_user = self.user_repo.get_by_email(email)
            if existing_user and (not linked_user or existing_user.id != linked_user.id):
                raise ValueError("Diese E-Mail-Adresse existiert bereits")

    def _sync_linked_user(self, member: Member, account_password: str | None = None) -> None:
        linked_user = self.user_repo.get_by_member_id(member.id)

        if member.role:
            if linked_user:
                update_data = {
                    "email": member.email,
                    "role": member.role,
                    "is_active": True,
                    "member_id": member.id,
                }
                if account_password:
                    update_data["password"] = account_password
                self.user_repo.update(linked_user.id, **update_data)
                return

            self.user_repo.create(
                username=self._generate_member_username(member),
                email=member.email,
                password=account_password,
                role=member.role,
                member_id=member.id,
                is_active=True,
            )
            return

        if linked_user:
            self.user_repo.update(
                linked_user.id,
                email=member.email,
                is_active=False,
                member_id=member.id,
            )
    
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
        account_password: str | None = None,
    ):
        """Create a new member"""
        self._validate_linked_user_state(
            email=email,
            role=role,
            linked_user=None,
            account_password=account_password,
        )
        member = self.repo.create(first_name, last_name, membership_number, email, phone, notes, has_discount, role)
        try:
            self._sync_linked_user(member, account_password)
            self.db.refresh(member)
            return member
        except Exception:
            self.db.rollback()
            if self.repo.get_by_id(member.id):
                self.repo.delete(member.id)
            raise
    
    def get_member(self, member_id: int):
        """Get member by ID"""
        return self.repo.get_by_id(member_id)
    
    def get_all_members(self):
        """Get all members"""
        return self.repo.get_all()
    
    def update_member(self, member_id: int, account_password: str | None = None, **kwargs):
        """Update member"""
        existing_member = self.repo.get_by_id(member_id)
        if not existing_member:
            return None

        linked_user = self.user_repo.get_by_member_id(member_id)
        self._validate_linked_user_state(
            email=kwargs.get("email", existing_member.email),
            role=kwargs.get("role", existing_member.role),
            linked_user=linked_user,
            account_password=account_password,
        )

        member = self.repo.update(member_id, **kwargs)
        if not member:
            return None

        self._sync_linked_user(member, account_password)
        self.db.refresh(member)
        return member
    
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

    def correct_balance(
        self,
        member_id: int,
        new_balance_cents: int,
        executed_by_username: str,
        reason: str | None = None,
    ):
        """Set member balance without cash flow and create a separate correction audit log."""
        member = self.repo.get_by_id(member_id)
        if not member:
            return None

        old_balance = member.balance_cents
        member.balance_cents = new_balance_cents
        correction_reason = (reason or "").strip() or "KORREKTURBUCHUNG"

        log = MemberBalanceCorrectionLog(
            member_id=member.id,
            member_name=member.name,
            old_balance_cents=old_balance,
            new_balance_cents=new_balance_cents,
            change_cents=new_balance_cents - old_balance,
            executed_by_username=executed_by_username,
            reason=correction_reason,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(member)
        self.db.refresh(log)
        return member

    def get_balance_correction_logs(self):
        """Get all member balance correction logs."""
        return (
            self.db.query(MemberBalanceCorrectionLog)
            .order_by(MemberBalanceCorrectionLog.created_at.desc(), MemberBalanceCorrectionLog.id.desc())
            .all()
        )
    
    def check_sufficient_balance(self, member_id: int, amount_cents: int) -> bool:
        """Check if member has sufficient balance"""
        member = self.repo.get_by_id(member_id)
        return member and member.balance_cents >= amount_cents
    
    def delete_member(self, member_id: int):
        """Delete member"""
        member = self.repo.get_by_id(member_id)
        if not member:
            return False

        linked_user = self.user_repo.get_by_member_id(member_id)

        # Keep historical transaction amounts, timestamps, and receipt metadata for statistics/audits while
        # removing only the deleted member foreign key reference.
        self.db.query(Transaction).filter(Transaction.member_id == member_id).update(
            {Transaction.member_id: None},
            synchronize_session=False,
        )
        self.db.query(BalanceLog).filter(BalanceLog.member_id == member_id).delete(synchronize_session=False)

        if linked_user:
            has_user_references = any([
                self.db.query(Transaction.id).filter(Transaction.user_id == linked_user.id).first(),
                self.db.query(CashEntry.id).filter(CashEntry.user_id == linked_user.id).first(),
                self.db.query(ClubAccountEntry.id).filter(ClubAccountEntry.user_id == linked_user.id).first(),
                self.db.query(MaterialAccountEntry.id).filter(MaterialAccountEntry.user_id == linked_user.id).first(),
                self.db.query(Deckel.id).filter(Deckel.created_by_user_id == linked_user.id).first(),
                self.db.query(Voucher.id).filter(Voucher.created_by_user_id == linked_user.id).first(),
                self.db.query(Voucher.id).filter(Voucher.redeemed_by_user_id == linked_user.id).first(),
            ])

            if has_user_references:
                self.user_repo.update(
                    linked_user.id,
                    is_active=False,
                    member_id=None,
                    email=None,
                )
            else:
                self.user_repo.delete(linked_user.id)

        delete_member_photo(member_id)
        return self.repo.delete(member_id)
