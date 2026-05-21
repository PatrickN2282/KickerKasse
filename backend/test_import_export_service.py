from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.constants import (
    INTERNAL_MATERIAL_CATEGORY_DESCRIPTION,
    INTERNAL_MATERIAL_CATEGORY_DISPLAY_ORDER,
    INTERNAL_MATERIAL_CATEGORY_NAME,
)
from app.models import Base, Category, Product, product_category
from app.services.import_export_service import ImportExportService


def test_import_service_can_replace_categories_and_products():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    fixed_category = Category(
        name=INTERNAL_MATERIAL_CATEGORY_NAME,
        description=INTERNAL_MATERIAL_CATEGORY_DESCRIPTION,
        display_order=INTERNAL_MATERIAL_CATEGORY_DISPLAY_ORDER,
        is_active_in_kasse=True,
    )
    old_category = Category(name="Alt", description="alt", display_order=1, is_active_in_kasse=True)
    old_product = Product(name="Altprodukt", price_cents=100, stock_quantity=1, is_active=True, tax_rate=19.0)
    old_product.categories = [old_category]
    session.add_all([fixed_category, old_category, old_product])
    session.commit()

    service = ImportExportService(session)
    import_payload = (
        "dataset,id,name,description,color,display_order,is_active_in_kasse\n"
        "categories,,Neu,Kategorie,#123456,2,true\n"
    ).encode("utf-8")
    product_payload = (
        "dataset,id,name,description,warengruppe,price_cents,member_price_cents,is_discountable,"
        "stock_quantity,is_unlimited_stock,is_variable_price,is_active,tax_rate,category_names\n"
        "products,,Neuprodukt,,Getränke,250,,true,3,false,false,true,19.0,Neu\n"
    ).encode("utf-8")

    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("categories.csv", import_payload)
        archive.writestr("products.csv", product_payload)

    result = service.import_sections(
        "import-export.zip",
        buffer.getvalue(),
        ["categories", "products"],
        replace_sections=["categories", "products"],
    )

    assert result["results"]["categories"]["replaced_deleted"] == 1
    assert result["results"]["products"]["replaced_deleted"] == 1

    categories = session.query(Category).order_by(Category.name).all()
    assert [category.name for category in categories] == [INTERNAL_MATERIAL_CATEGORY_NAME, "Neu"]

    products = session.query(Product).all()
    assert [product.name for product in products] == ["Neuprodukt"]
    assert [category.name for category in products[0].categories] == ["Neu"]
    assert session.execute(product_category.select()).all()
