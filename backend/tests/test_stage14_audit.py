"""Etappe 14: prepared for the final combined acceptance; not run on 08.09.2026."""
import asyncio
import json
import pytest
from app.models import AuditLog, Member, User, UserRole, Product, Category
from app.services.audit_log_service import AuditLogService
from app.services.product_service import ProductService
from app.services.member_service import MemberService
from app.services.user_service import UserService
from app.services.app_settings_service import AppSettingsService
from app.schemas.category import CategoryUpdate
from app.api.category import update_category
from starlette.requests import Request
from .test_stage789_bookings import booking_db, seed, fail


@pytest.mark.parametrize("operation", ["product_create", "product_update", "stock", "member_create",
    "member_role", "balance", "user_create", "user_role", "settings", "category"])
@pytest.mark.parametrize("failure", ["audit", "commit"])
def test_master_data_and_audit_rollback_together(booking_db, monkeypatch, operation, failure):
    db = booking_db
    actor, product = seed(db)
    member = MemberService(db).create_member("Audit", "Mitglied", role="MANAGER", account_password="Test-only-123!")
    user = UserService(db).create_user("audit-direct", None, "Test-only-123!", "MANAGER")
    settings = AppSettingsService(db).get_or_create_settings()
    category = Category(name="Vorher")
    db.add(category); db.commit()
    ids = actor.id, product.id, member.id, user.id, category.id
    audit_count = db.query(AuditLog).count()
    user_count, member_count, product_count = db.query(User).count(), db.query(Member).count(), db.query(Product).count()
    linked = db.query(User).filter_by(member_id=member.id).one()
    linked_version = linked.session_version
    recipient = settings.email_recipient_backup
    request = Request({"type": "http", "headers": [], "session": {
        "user_id": actor.id, "session_version": actor.session_version}})
    operations = {
        "product_create": lambda: ProductService(db).create_product("Neu", 100, performed_by_username=actor.username),
        "product_update": lambda: ProductService(db).update_product(product.id, name="Neu"),
        "stock": lambda: ProductService(db).adjust_stock(product.id, 2),
        "member_create": lambda: MemberService(db).create_member("Neu", "Konto", role="ADMIN", account_password="Test-only-123!"),
        "member_role": lambda: MemberService(db).update_member(member.id, role="ADMIN"),
        "balance": lambda: MemberService(db).correct_balance(member.id, 100, executed_by_user_id=actor.id, reason="Testkorrektur"),
        "user_create": lambda: UserService(db).create_user("Neu", None, "Test-only-123!"),
        "user_role": lambda: UserService(db).update_user(user.id, role="ADMIN"),
        "settings": lambda: AppSettingsService(db).update_settings(email_recipient_backup="neu@example.test"),
        "category": lambda: asyncio.run(update_category(category.id, CategoryUpdate(name="Neu"), request, db)),
    }
    with monkeypatch.context() as patch:
        if failure == "audit":
            patch.setattr(AuditLogService, "log", fail)
        else:
            patch.setattr(db, "commit", fail)
        with pytest.raises(RuntimeError):
            operations[operation]()
    db.expire_all()
    assert db.query(AuditLog).count() == audit_count
    assert (db.query(User).count(), db.query(Member).count(), db.query(Product).count()) == (user_count, member_count, product_count)
    assert db.get(Product, ids[1]).name == "Testartikel"
    assert db.get(Product, ids[1]).stock_quantity == 20
    assert db.get(Member, ids[2]).balance_cents == 0
    assert db.get(Member, ids[2]).role == UserRole.MANAGER
    assert db.get(User, ids[3]).role == UserRole.MANAGER
    assert db.query(User).filter_by(member_id=ids[2]).one().session_version == linked_version
    assert db.get(Category, ids[4]).name == "Vorher"
    assert AppSettingsService(db).get_or_create_settings().email_recipient_backup == recipient


def test_recipients_and_secret_replacement_are_logged_without_secret(db_session):
    service = AppSettingsService(db_session)
    service.update_settings(performed_by_username="chef", smtp_password="first-secret", email_recipient_backup="alt@example.test")
    service.update_settings(performed_by_username="chef", smtp_password="second-secret", email_recipient_backup="neu@example.test")
    entry = db_session.query(AuditLog).order_by(AuditLog.id.desc()).first()
    assert entry.user_username == "chef"
    assert json.loads(entry.old_value)["email_recipient_backup"] == "alt@example.test"
    assert json.loads(entry.new_value)["email_recipient_backup"] == "neu@example.test"
    assert "smtp_password" in json.loads(entry.new_value)
    assert "first-secret" not in entry.old_value and "second-secret" not in entry.new_value
    entry = AuditLogService(db_session).log(entity_type="test", action="TEST", new_value={
        "nested": [{"password_hash": "hash-secret", "auth_password": "clear-secret"}]})
    assert "hash-secret" not in entry.new_value and "clear-secret" not in entry.new_value


def test_optional_audit_failure_is_visible(db_session, monkeypatch, caplog):
    monkeypatch.setattr(AuditLogService, "log", fail)
    assert AuditLogService(db_session).log_optional(entity_type="export", action="EXPORTED") is False
    assert "Optional audit event failed: export/EXPORTED" in caplog.text


def test_member_role_audit_contains_linked_account_and_password_flag(db_session):
    member = MemberService(db_session).create_member("Audit", "Konto", role="MANAGER", account_password="Old-password-123!")
    MemberService(db_session).update_member(member.id, role="ADMIN", account_password="New-password-123!", performed_by_username="chef")
    entry = db_session.query(AuditLog).order_by(AuditLog.id.desc()).first()
    assert json.loads(entry.old_value)["linked_account"]["role"] == "MANAGER"
    assert json.loads(entry.new_value)["linked_account"]["role"] == "ADMIN"
    assert json.loads(entry.new_value)["account_password_changed"] is True
    assert "New-password" not in entry.new_value


def test_media_returns_to_old_generation_on_commit_failure(db_session, monkeypatch, tmp_path):
    from app.core.atomic import audited_media
    from app.services import file_service
    monkeypatch.setattr(file_service, "UPLOADS_DIR", tmp_path)
    monkeypatch.setattr(file_service, "PRODUCTS_DIR", tmp_path / "products")
    folder = tmp_path / "products" / "1"
    folder.mkdir(parents=True); (folder / "image.png").write_bytes(b"old")
    @audited_media("products", "product_id")
    async def change(product_id, db):
        (folder / "image.png").write_bytes(b"new")
        AuditLogService(db).log(entity_type="product", action="IMAGE_UPDATED")
    monkeypatch.setattr(db_session, "commit", fail)
    with pytest.raises(RuntimeError):
        asyncio.run(change(1, db_session))
    assert (folder / "image.png").read_bytes() == b"old"
    assert db_session.query(AuditLog).count() == 0
