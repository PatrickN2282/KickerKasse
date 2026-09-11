"""Etappe 15: deferred PostgreSQL roundtrip, rejection, lock and recovery tests.

Only isolated databases provided by pg_engine are used. These tests have NOT been
executed as part of the implementation on 08.09.2026.
"""
import hashlib
import io
import json
import zipfile
from uuid import uuid4
from datetime import datetime
import pytest
from fastapi import HTTPException
from sqlalchemy import event, text
from sqlalchemy.orm import Session
from app.core.db_migration import run_migrations
from app.core.maintenance_lock import maintenance_gate
from app.models import Product, Member, User, AuditLog, Transaction, ZBonHistory
from app.services.database_backup_service import DatabaseBackupService, canonical
from app.services.backup_media import MediaReplacement, recover_media, recovery_pending
from app.services.member_service import MemberService
from app.services.app_settings_service import AppSettingsService
from .test_stage789_bookings import seed, sale, fail


@pytest.fixture
def backup_fixture(pg_engine, tmp_path):
    assert run_migrations(pg_engine)
    with Session(pg_engine, autoflush=False) as db:
        user, product = seed(db)
        member = MemberService(db).create_member("Backup", "Mitglied")
        member.balance_cents = 12345
        member.photo_path = "members/1/photo.png"
        product.image_path = "products/1/image.png"
        settings = AppSettingsService(db).get_or_create_settings()
        settings.logo_path = "app_settings/logo.png"
        db.commit()
        for name, data in {"members/1/photo.png": b"photo", "products/1/image.png": b"product",
                           "products/1/original.png": b"original", "app_settings/logo.png": b"logo"}.items():
            path = tmp_path / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        sale(db, user, product, member_id=member.id)
        archived = ZBonHistory(sequence_number=1, business_date=datetime(2026, 9, 8),
            period_start=datetime(2026, 9, 8), period_end=datetime(2026, 9, 8, 23, 59),
            report_content="<html>Unverändertes Z-Bon-Archiv</html>", report_data='{"snapshot": true}')
        db.add(archived); db.flush()
        db.query(Transaction).one().zbon_history_id = archived.id
        db.commit()
        service = DatabaseBackupService(db, tmp_path)
        content, filename = service.create_backup_zip()
        yield db, service, content, filename, (user.id, product.id, member.id)


def rewrite(content, change):
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    payload = json.loads(entries["backup.json"])
    change(payload, entries)
    # Deliberately recalculate hashes: validation must not rely only on checksums.
    for table in payload["tables"]:
        table["row_count"] = len(table["rows"])
        table["sha256"] = hashlib.sha256(canonical(table["rows"])).hexdigest()
    entries["backup.json"] = canonical(payload)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, data in entries.items(): archive.writestr(name, data)
    return output.getvalue()


def test_complete_roundtrip_to_fresh_postgres(backup_fixture, tmp_path):
    from .conftest import pg_engine as engine_fixture
    source, service, content, filename, ids = backup_fixture
    # A second independent disposable database, never the configured application DB.
    generator = engine_fixture.__wrapped__()
    target_engine = next(generator)
    try:
        assert run_migrations(target_engine)
        target_media = tmp_path / "restored"
        with Session(target_engine) as target:
            result = DatabaseBackupService(target, target_media).restore_from_backup_zip(filename, content, actor_username="operator")
            assert result["restored_media_files"] == 4
            assert target.get(Member, ids[2]).balance_cents == 12345
            assert target.get(Product, ids[1]).stock_quantity == 19
            assert target.get(User, ids[0]).password_hash == source.get(User, ids[0]).password_hash
            assert target.query(ZBonHistory).one().report_content == "<html>Unverändertes Z-Bon-Archiv</html>"
            assert target.query(Transaction).one().zbon_history_id == target.query(ZBonHistory).one().id
            assert target.query(Transaction).one().receipt_number == source.query(Transaction).one().receipt_number
            assert (target_media / "app_settings/logo.png").read_bytes() == b"logo"
            assert (target_media / "members/1/photo.png").read_bytes() == b"photo"
            assert (target_media / "products/1/original.png").read_bytes() == b"original"
            new_product = Product(name="Nach Restore", price_cents=1)
            target.add(new_product); target.commit()
            assert new_product.id > ids[1]
            assert target.query(AuditLog).filter_by(action="RESTORED", user_username="operator").count() == 1
    finally:
        generator.close()


@pytest.mark.parametrize("damage", ["missing_table", "duplicate_table", "column", "schema", "fk", "constraint", "missing_media", "media_hash", "path", "old_format"])
def test_invalid_archive_rejected_before_truncate(backup_fixture, damage):
    db, service, content, filename, ids = backup_fixture
    def corrupt(payload, entries):
        member = next(table for table in payload["tables"] if table["name"] == "members")
        if damage == "missing_table": payload["tables"].pop()
        if damage == "duplicate_table": payload["tables"].append(payload["tables"][0])
        if damage == "column": member["rows"][0].pop("balance_cents")
        if damage == "schema": payload["schema"]["migrations"] = []
        if damage == "fk":
            next(table for table in payload["tables"] if table["name"] == "transactions")["rows"][0]["user_id"] = 999999
        if damage == "constraint": member["rows"][0]["balance_cents"] = -1
        if damage == "missing_media": entries.pop("media/app_settings/logo.png")
        if damage == "media_hash": entries["media/app_settings/logo.png"] = b"damaged"
        if damage == "path": entries["media/../outside"] = b"bad"
        if damage == "old_format": payload["format"] = "kickerkasse-db-backup-v1"
    damaged = rewrite(content, corrupt)
    executed = []
    def record(conn, cursor, statement, parameters, context, executemany): executed.append(statement)
    event.listen(service.engine, "before_cursor_execute", record)
    try:
        with pytest.raises(HTTPException): service.restore_from_backup_zip(filename, damaged)
    finally:
        event.remove(service.engine, "before_cursor_execute", record)
    assert not any("TRUNCATE" in statement.upper() for statement in executed)
    assert db.get(Member, ids[2]).balance_cents == 12345
    assert (service.uploads_dir / "app_settings/logo.png").read_bytes() == b"logo"


@pytest.mark.parametrize("failure", ["audit", "media", "commit"])
def test_restore_failure_keeps_current_db_and_media(backup_fixture, monkeypatch, failure):
    from app.services.audit_log_service import AuditLogService
    db, service, content, filename, ids = backup_fixture
    db.get(Member, ids[2]).balance_cents = 777; db.commit()
    logo = service.uploads_dir / "app_settings/logo.png"; logo.write_bytes(b"current-logo")
    old_apply = MediaReplacement.apply
    def broken_apply(self, source="new"):
        old_apply(self, source)
        if source == "new": raise RuntimeError("media failure")
    with monkeypatch.context() as patch:
        if failure == "audit": patch.setattr(AuditLogService, "log", fail)
        if failure == "media": patch.setattr(MediaReplacement, "apply", broken_apply)
        if failure == "commit": patch.setattr(db, "commit", fail)
        with pytest.raises(RuntimeError): service.restore_from_backup_zip(filename, content)
    assert db.get(Member, ids[2]).balance_cents == 777
    assert logo.read_bytes() == b"current-logo"
    assert not recovery_pending(service.uploads_dir)


@pytest.mark.parametrize("committed", [False, True])
def test_restart_recovers_matching_media_generation(backup_fixture, committed):
    db, service, _, _, _ = backup_fixture
    replacement = MediaReplacement(service.uploads_dir, str(uuid4()))
    replacement.prepare({"new.png": b"new"})
    replacement.apply()
    if committed:
        from app.services.audit_log_service import AuditLogService
        AuditLogService(db).log(entity_type="database_backup", action="RESTORED", entity_name=replacement.operation_id)
        db.commit()
    recover_media(db, service.uploads_dir)
    assert not recovery_pending(service.uploads_dir)
    assert (service.uploads_dir / "new.png").exists() is committed
    assert (service.uploads_dir / "app_settings/logo.png").exists() is (not committed)


def test_gate_excludes_concurrent_requests_and_restore(backup_fixture):
    db, service, content, filename, _ = backup_fixture
    with maintenance_gate(service.engine):
        with pytest.raises(HTTPException): service.restore_from_backup_zip(filename, content)
    with maintenance_gate(service.engine, exclusive=True):
        with pytest.raises(HTTPException):
            with maintenance_gate(service.engine): pass
    with maintenance_gate(service.engine): pass


def test_archive_size_and_extraction_limits(monkeypatch):
    import app.services.database_backup_service as backup
    monkeypatch.setattr(backup, "MAX_ARCHIVE_BYTES", 4)
    with pytest.raises(HTTPException) as exc:
        backup.DatabaseBackupService._read_archive(b"12345")
    assert exc.value.status_code == 413
    monkeypatch.setattr(backup, "MAX_ARCHIVE_BYTES", 100000)
    monkeypatch.setattr(backup, "MAX_EXPANDED_BYTES", 4)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("backup.json", b"0" * 5000)
    with pytest.raises(HTTPException): backup.DatabaseBackupService._read_archive(output.getvalue())


def test_snapshot_blocks_background_writes_until_capture_finishes(backup_fixture, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    db, service, _, _, ids = backup_fixture
    reached_snapshot, release_snapshot, writer_started = Event(), Event(), Event()
    original_schema = DatabaseBackupService._schema
    def pause(self, metadata):
        reached_snapshot.set()
        assert release_snapshot.wait(10)
        return original_schema(self, metadata)
    monkeypatch.setattr(DatabaseBackupService, "_schema", pause)
    def export():
        with Session(service.engine) as isolated:
            return DatabaseBackupService(isolated, service.uploads_dir).create_backup_zip()[0]
    def write():
        with Session(service.engine) as isolated:
            writer_started.set()
            isolated.execute(text("UPDATE products SET stock_quantity = 9 WHERE id=:id"), {"id": ids[1]})
            isolated.execute(text("UPDATE members SET balance_cents = 900 WHERE id=:id"), {"id": ids[2]})
            isolated.commit()
    db.rollback()
    with ThreadPoolExecutor(max_workers=2) as executor:
        capture = executor.submit(export)
        assert reached_snapshot.wait(10)
        writer = executor.submit(write)
        try:
            assert writer_started.wait(10)
            assert not writer.done()
        finally:
            release_snapshot.set()
        content = capture.result(timeout=15)
        writer.result(timeout=15)
    payload, _ = DatabaseBackupService._read_archive(content)
    product = next(table for table in payload["tables"] if table["name"] == "products")["rows"][0]
    member = next(table for table in payload["tables"] if table["name"] == "members")["rows"][0]
    assert product["stock_quantity"] == 19 and member["balance_cents"] == 12345
    db.expire_all()
    assert db.get(Product, ids[1]).stock_quantity == 9
    assert db.get(Member, ids[2]).balance_cents == 900
