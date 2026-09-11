"""Etappe 16: only prepared, not executed; run during combined final acceptance."""
import csv
import io
import pytest
from fastapi import HTTPException
from app.models import Category, Product, Member, User, UserRole, Deckel, DeckelItem, AuditLog
from app.services.import_export_service import ImportExportService
from app.services.member_service import MemberService
from app.services.audit_log_service import AuditLogService
from app.services import file_service
from .test_stage789_bookings import booking_db, fail


def csv_data(section, **values):
    output = io.StringIO()
    row = {"dataset": section, **values}
    writer = csv.DictWriter(output, fieldnames=list(row))
    writer.writeheader(); writer.writerow(row)
    return output.getvalue().encode("utf-8-sig")


@pytest.fixture
def media_root(tmp_path, monkeypatch):
    import app.services.import_export_service as transfer
    monkeypatch.setattr(file_service, "UPLOADS_DIR", tmp_path)
    for name, section in (("PRODUCTS_DIR", "products"), ("MEMBERS_DIR", "members"), ("APP_SETTINGS_DIR", "app_settings")):
        monkeypatch.setattr(file_service, name, tmp_path / section)
        if hasattr(transfer, name): monkeypatch.setattr(transfer, name, tmp_path / section)
    return tmp_path


def test_foreign_id_never_overwrites_other_product(booking_db, media_root):
    db = booking_db
    product = Product(name="Original", price_cents=500, stock_quantity=2)
    db.add(product); db.commit(); identifier = product.id
    data = csv_data("products", id=identifier, name="Fremd", price_cents=100, stock_quantity=0)
    service = ImportExportService(db)
    plan = service.analyze_import("products.csv", data)
    assert not plan["conflicts"] and plan["records"][0]["action"] == "create"
    service.import_sections("products.csv", data)
    assert db.get(Product, identifier).name == "Original"
    assert db.query(Product).filter_by(name="Fremd").one().id != identifier


def test_same_id_name_mismatch_is_reported_before_mutation(booking_db, media_root):
    db = booking_db
    product = Product(name="Original", price_cents=500)
    db.add(product); db.commit()
    data = csv_data("products", id=product.id, name="Fremd", price_cents=100, stock_quantity=0)
    service = ImportExportService(db)
    assert service.analyze_import("products.csv", data, source_mode="same")["conflicts"]
    with pytest.raises(HTTPException): service.import_sections("products.csv", data, source_mode="same")
    assert db.query(Product).one().name == "Original"


def test_open_deckel_blocks_replacement_and_keeps_media(booking_db, media_root):
    from app.services.deckel_service import DeckelService
    from .test_stage789_bookings import seed
    db = booking_db
    user, product = seed(db)
    deckel = DeckelService(db).create_deckel("Offen", user.id, [{"product_id": product.id, "quantity": 1, "unit_price_cents": 500}])
    product.stock_quantity = 0; db.commit()
    path = media_root / "products" / str(product.id) / "image.png"
    path.parent.mkdir(parents=True); path.write_bytes(b"keep")
    data = csv_data("products", id=100, name="Neu", price_cents=100, stock_quantity=0)
    with pytest.raises(HTTPException):
        ImportExportService(db).import_sections("products.csv", data, replace_sections=["products"])
    assert db.query(DeckelItem).count() == 1 and path.read_bytes() == b"keep"


@pytest.mark.parametrize("linked", [False, True])
def test_members_with_balance_or_account_cannot_be_replaced(booking_db, media_root, linked):
    db = booking_db
    member = MemberService(db).create_member("Alt", "Mitglied")
    if linked:
        db.add(User(username="linked", password_hash="unused", role=UserRole.MANAGER, member_id=member.id))
    else:
        member.balance_cents = 500
    db.commit()
    data = csv_data("members", id=100, first_name="Neu", last_name="Mitglied", balance_cents=0)
    with pytest.raises(HTTPException):
        ImportExportService(db).import_sections("members.csv", data, replace_sections=["members"])
    assert db.query(Member).one().first_name == "Alt"


def test_initial_values_need_explicit_acknowledgement(booking_db, media_root):
    service = ImportExportService(booking_db)
    data = csv_data("members", id=1, first_name="Neu", last_name="Mitglied", balance_cents=1200)
    assert service.analyze_import("members.csv", data)["initial_balance_cents"] == 1200
    with pytest.raises(HTTPException): service.import_sections("members.csv", data)
    assert booking_db.query(Member).count() == 0
    service.import_sections("members.csv", data, acknowledge_initial_values=True)
    assert booking_db.query(Member).one().balance_cents == 1200


def test_analysis_is_rechecked_against_changed_stock(booking_db, media_root):
    db = booking_db
    product = Product(name="Artikel", price_cents=100, stock_quantity=1)
    db.add(product); db.commit()
    data = csv_data("products", id=product.id, name="Artikel", price_cents=200, stock_quantity=1)
    service = ImportExportService(db)
    assert not service.analyze_import("products.csv", data, source_mode="same")["conflicts"]
    product.stock_quantity = 2; db.commit()
    with pytest.raises(HTTPException): service.import_sections("products.csv", data, source_mode="same")
    assert db.query(Product).one().price_cents == 100


def test_full_product_and_original_media_roundtrip(db_session, media_root):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.models import Base
    category = Category(name="Kategorie | mit Trennzeichen")
    product = Product(name="AVIF Produkt", price_cents=1234, member_price_cents=900, stock_quantity=7,
        minimum_stock_quantity=3, notify_on_low_stock=True, requires_guest_list=True,
        opens_small_parts_drawer=True, is_variable_price=True, is_discountable=False,
        tax_rate=19, warengruppe="Exportgruppe", categories=[category])
    db_session.add(product); db_session.commit()
    folder = media_root / "products" / str(product.id); folder.mkdir(parents=True)
    (folder / "image.webp").write_bytes(b"main")
    (folder / "original.avif").write_bytes(b"original-avif")
    product.image_path = f"products/{product.id}/image.webp"; db_session.commit()
    content, _, filename = ImportExportService(db_session).export_sections(["categories", "products"], True)
    engine = create_engine("sqlite:///:memory:"); Base.metadata.create_all(engine)
    try:
        with Session(engine, autoflush=False) as target:
            # Force different target IDs to exercise media association through source IDs.
            target.add(Product(name="Existing", price_cents=1)); target.commit()
            ImportExportService(target).import_sections(filename, content, import_media=True, acknowledge_initial_values=True)
            restored = target.query(Product).filter_by(name="AVIF Produkt").one()
            for field in ("price_cents", "member_price_cents", "stock_quantity", "minimum_stock_quantity",
                          "notify_on_low_stock", "requires_guest_list", "opens_small_parts_drawer",
                          "is_variable_price", "is_discountable", "tax_rate", "warengruppe"):
                assert getattr(restored, field) == getattr(product, field)
            assert restored.categories[0].name == category.name
            assert (media_root / restored.image_path).read_bytes() == b"main"
            assert (media_root / "products" / str(restored.id) / "original.avif").read_bytes() == b"original-avif"
    finally:
        engine.dispose()


@pytest.mark.parametrize("failure", ["audit", "commit", "media"])
def test_failure_rolls_back_import_and_media(booking_db, media_root, monkeypatch, failure):
    from app.services.backup_media import MediaReplacement
    db = booking_db
    path = media_root / "keep.png"; path.write_bytes(b"old")
    data = csv_data("products", id=1, name="Neu", price_cents=100, stock_quantity=0)
    original_apply = MediaReplacement.apply
    def broken(self, source="new"):
        original_apply(self, source)
        if source == "new": raise RuntimeError("media")
    with monkeypatch.context() as patch:
        if failure == "audit": patch.setattr(AuditLogService, "log", fail)
        if failure == "commit": patch.setattr(db, "commit", fail)
        if failure == "media": patch.setattr(MediaReplacement, "apply", broken)
        with pytest.raises(RuntimeError): ImportExportService(db).import_sections("products.csv", data)
    assert db.query(Product).count() == 0
    assert db.query(AuditLog).count() == 0
    assert path.read_bytes() == b"old"


def test_unknown_version_and_duplicate_zip_paths_rejected(db_session):
    import zipfile
    service = ImportExportService(db_session)
    data = csv_data("products", transfer_version="999", name="Neu", price_cents=1, stock_quantity=0)
    with pytest.raises(HTTPException): service.analyze_import("products.csv", data)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("../outside.csv", b"bad")
    with pytest.raises(HTTPException): service.analyze_import("data.zip", buffer.getvalue())


@pytest.mark.parametrize("role,expected", [(UserRole.ADMIN, 403), (UserRole.MANAGER, 403), (UserRole.TOP_ADMIN, 200)])
def test_http_import_permission_and_actor(db_session, monkeypatch, role, expected):
    import asyncio
    import httpx
    from app.api.import_export import router
    from .test_stage1112_bookings import make_app
    user = User(username="transfer-actor", password_hash="unused", role=role)
    db_session.add(user); db_session.commit()
    app = make_app(db_session); app.include_router(router)
    calls = []
    def import_stub(self, *args, **kwargs):
        calls.append(kwargs)
        return {"results": {}, "imported_sections": []}
    monkeypatch.setattr(ImportExportService, "import_sections", import_stub)
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://isolated") as client:
            await client.get(f"/test-session/{user.id}")
            response = await client.post("/api/admin/import-export/import", files={"data_file": ("products.csv", b"test")},
                                         data={"source_mode": "foreign"})
            assert response.status_code == expected
    asyncio.run(exercise())
    assert bool(calls) is (expected == 200)
    if calls: assert calls[0]["actor_username"] == "transfer-actor"


def test_separate_original_can_supplement_embedded_main(db_session):
    service = ImportExportService(db_session)
    main = {"products": {"1": {"files": [{"filename": "image.png", "content": b"main", "variant": "main"}]}}}
    original = {"products": {"1": {"files": [{"filename": "original.avif", "content": b"original", "variant": "original"}]}}}
    merged = service._merge_media_entries(main, original)
    assert {item["variant"] for item in merged["products"]["1"]["files"]} == {"main", "original"}
    with pytest.raises(HTTPException): service._merge_media_entries(main, main)
