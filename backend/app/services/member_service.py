from app.core.atomic import audited_change
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
from app.services.actor_resolution_service import resolve_actor_username
from app.services.file_service import delete_member_photo
from app.models.user import parse_user_role, UserRole


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

    @staticmethod
    def _role_value(role) -> str | None:
        return getattr(role, "value", role)

    def _sync_member_username(self, member: Member, linked_user) -> None:
        """Keep linked user usernames aligned with the current member name.

        Imported data can leave historical usernames behind. When a member later receives a
        role again, we prefer to reuse the current name-based username if possible and fall
        back to a collision-safe suffix otherwise.
        """
        target_username = self._generate_member_username(member)
        if linked_user.username == target_username:
            return
        self.user_repo.update(linked_user.id, username=target_username)

    def _resolve_linked_user_email(self, email: str | None, linked_user=None) -> str | None:
        normalized_email = (email or "").strip() or None
        if not normalized_email:
            return None

        existing_user = self.user_repo.get_by_email(normalized_email)
        if existing_user and (not linked_user or existing_user.id != linked_user.id):
            return None
        return normalized_email

    def _validate_linked_user_state(
        self,
        *,
        email: str | None,
        role,
        linked_user,
        account_password: str | None,
        existing_member: Member | None = None,
    ) -> None:
        normalized_role = parse_user_role(role)
        if normalized_role == "TOP_ADMIN":
            raise ValueError("Top-Admin kann nicht an Mitglieder vergeben werden")
        if linked_user and linked_user.role == UserRole.TOP_ADMIN:
            raise ValueError("Top-Admin kann nicht über die Mitgliederverwaltung geändert werden")

        # Imported members can retain a role without a recreated user account. In that case we
        # allow ordinary member edits without forcing a password prompt; account creation still
        # requires an explicit password when a new linked user is actually being created.
        role_requires_password = normalized_role and not linked_user and not account_password
        existing_role = self._role_value(existing_member.role) if existing_member else None
        if role_requires_password and not (existing_member and existing_role == normalized_role):
            raise ValueError("Mitglieder mit Rolle benötigen ein Passwort für den Benutzerzugang")

        # Member emails are intentionally independent from user emails.
        # If a linked user must be synced and the email is already used by another
        # user account, we keep member editing functional and store no user email.

    def _sync_linked_user(self, member: Member, account_password: str | None = None, *, role_changed: bool = False) -> None:
        linked_user = self.user_repo.get_by_member_id(member.id)
        target_email = self._resolve_linked_user_email(member.email, linked_user)

        if linked_user:
            update_data = {
                "username": self._generate_member_username(member),
                "email": target_email,
            }
            # Profile/password edits must never grant a role or reactivate a login.
            # Only a deliberate change of the member role changes access state.
            if role_changed:
                update_data["is_active"] = bool(member.role)
                if member.role:
                    update_data["role"] = member.role
            if account_password:
                update_data["password"] = account_password
            self.user_repo.update(linked_user.id, **update_data)
            return

        if member.role and account_password:
            self.user_repo.create(
                username=self._generate_member_username(member),
                email=target_email,
                password=account_password,
                role=member.role,
                member_id=member.id,
                is_active=True,
            )
            return

    
    @audited_change
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
            existing_member=None,
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
                    "role": self._role_value(member.role),
                    "account_password_changed": bool(account_password),
                    "phone": phone,
                    "notes": notes,
                },
            )
            self.db.commit()
            self.db.refresh(member)
            return member
        except Exception:
            self.db.rollback()
            raise
    
    def get_member(self, member_id: int):
        """Get member by ID"""
        return self.repo.get_by_id(member_id, include_archived=True)
    
    def get_all_members(self, *, include_archived=False):
        """Get all members"""
        return self.repo.get_all(include_archived=include_archived)
    
    @audited_change
    def update_member(self, member_id: int, account_password: str | None = None, performed_by_username: str | None = None, **kwargs):
        """Update member"""
        if "balance_cents" in kwargs:
            raise ValueError("Guthaben bitte über Aufladung oder Guthabenkorrektur ändern")

        existing_member = self.repo.get_by_id(member_id)
        if not existing_member:
            return None

        from app.schemas.validation import validate_member_name
        validate_member_name(kwargs.get("first_name", existing_member.first_name), kwargs.get("last_name", existing_member.last_name))

        old_snapshot = {
            "name": existing_member.name,
            "role": self._role_value(existing_member.role),
            "email": existing_member.email,
            "membership_number": existing_member.membership_number,
            "has_discount": existing_member.has_discount,
            "notes": existing_member.notes,
            "first_name": existing_member.first_name,
            "last_name": existing_member.last_name,
            "phone": existing_member.phone,
        }

        linked_user = self.user_repo.get_by_member_id(member_id)
        from app.services.user_service import UserService
        old_snapshot["linked_account"] = UserService._snapshot_user(linked_user) if linked_user else None
        self._validate_linked_user_state(
            email=kwargs.get("email", existing_member.email),
            role=kwargs.get("role", existing_member.role),
            linked_user=linked_user,
            account_password=account_password,
            existing_member=existing_member,
        )

        role_changed = "role" in kwargs and parse_user_role(kwargs["role"]) != existing_member.role
        member = self.repo.update(member_id, **kwargs)
        if not member:
            return None

        self._sync_linked_user(member, account_password, role_changed=role_changed)
        self.db.refresh(member)
        linked_user = self.user_repo.get_by_member_id(member_id)
        self._audit("UPDATED", member, performed_by_username, old_value=old_snapshot,
            new_value={**kwargs, "account_password_changed": bool(account_password),
                "linked_account": UserService._snapshot_user(linked_user) if linked_user else None})
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def recharge_balance(
        self, member_id: int, amount_cents: int, reason: str = "RECHARGE",
        executed_by_username: str | None = None, *, executed_by_user_id: int,
    ):
        """Persist balance, cash transaction and both histories as a single booking."""
        from app.models import TransactionType, PaymentMethod
        from app.repositories import TransactionRepository
        from app.services.audit_log_service import AuditLogService
        from app.schemas.validation import MAX_INT
        try:
            if not isinstance(amount_cents, int) or not 0 < amount_cents <= MAX_INT:
                raise ValueError("Aufladebetrag muss positiv sein und im zulässigen Bereich liegen")
            member = self.repo.get_by_id_for_update(member_id)
            if not member:
                return None
            old_balance = member.balance_cents
            if old_balance + amount_cents > MAX_INT:
                raise ValueError("Das resultierende Guthaben ist zu groß")
            member.balance_cents += amount_cents
            transaction = TransactionRepository(self.db).create(
                type=TransactionType.RECHARGE, payment_method=PaymentMethod.CASH,
                total_amount_cents=amount_cents, user_id=executed_by_user_id,
                member_id=member.id, member_name=member.name,
                performed_by_username=executed_by_username, items=[], commit=False,
            )
            self.balance_log_repo.create(member_id=member.id, old_balance_cents=old_balance,
                                         new_balance_cents=member.balance_cents, reason=reason,
                                         transaction_id=transaction.id, commit=False)
            AuditLogService(self.db).log(
                entity_type="member", action="RECHARGED", user_username=executed_by_username,
                entity_id=member.id, entity_name=member.name,
                old_value={"balance_cents": old_balance},
                new_value={"balance_cents": member.balance_cents, "change_cents": amount_cents,
                           "reason": reason, "transaction_id": transaction.id},
            )
            self.db.commit()
            self.db.refresh(member)
            return member
        except Exception:
            self.db.rollback()
            raise

    @audited_change
    def correct_balance(
        self,
        member_id: int,
        new_balance_cents: int,
        executed_by_username: str | None = None,
        executed_by_user_id: int | None = None,
        reason: str | None = None,
    ):
        """Set member balance without cash flow and create a separate correction audit log."""
        from app.core.financial_booking import lock_financial_period
        lock_financial_period(self.db)
        member = self.repo.get_by_id_for_update(member_id)
        if not member:
            return None

        actor_username = resolve_actor_username(
            self.db,
            executed_by_username=executed_by_username,
            executed_by_user_id=executed_by_user_id,
        )

        old_balance = member.balance_cents
        member.balance_cents = new_balance_cents
        correction_reason = (reason or "").strip() or "KORREKTURBUCHUNG"

        log = MemberBalanceCorrectionLog(
            member_id=member.id,
            member_name=member.name,
            old_balance_cents=old_balance,
            new_balance_cents=new_balance_cents,
            change_cents=new_balance_cents - old_balance,
            executed_by_username=actor_username or "Unbekannt",
            reason=correction_reason,
        )
        self.db.add(log)
        self._audit(
            "BALANCE_CORRECTION",
            member,
            actor_username,
            old_value={"balance_cents": old_balance},
            new_value={
                "balance_cents": new_balance_cents,
                "change_cents": new_balance_cents - old_balance,
                "reason": correction_reason,
            },
        )
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
        """Compatibility endpoint: archive without erasing financial or guest history."""
        return self.set_archived(member_id, True, performed_by_username)

    @audited_change
    def set_archived(self, member_id: int, archived: bool, performed_by_username=None):
        from datetime import datetime
        from app.core.financial_booking import lock_financial_period
        from app.services.audit_log_service import AuditLogService
        try:
            lock_financial_period(self.db)
            member = self.db.query(Member).filter(Member.id == member_id).populate_existing().with_for_update().first()
            if not member:
                return False
            if bool(member.archived_at) == archived:
                return True
            if archived and member.balance_cents != 0:
                raise ValueError("Vor der Archivierung das Restguthaben fachlich klären und über den vorgesehenen Korrekturweg dokumentieren.")
            linked_user = self.user_repo.get_by_member_id(member_id)
            if member.role == UserRole.TOP_ADMIN or (linked_user and linked_user.role == UserRole.TOP_ADMIN):
                raise ValueError("Ein Top-Admin-Mitglied kann nicht archiviert werden. Zuerst den geschützten Zugang über die Benutzerverwaltung klären.")
            old = {"archived": bool(member.archived_at), "balance_cents": member.balance_cents}
            member.archived_at = datetime.now() if archived else None
            if archived and linked_user:
                linked_user.is_active = False
            # Reactivation never silently restores a previously disabled login.
            AuditLogService(self.db).log(entity_type="member", action="ARCHIVED" if archived else "RESTORED",
                user_username=performed_by_username, entity_id=member.id, entity_name=member.name,
                old_value=old, new_value={"archived": archived, "balance_cents": member.balance_cents})
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise
