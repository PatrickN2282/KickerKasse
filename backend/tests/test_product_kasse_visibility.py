from app.models import Product
from app.core.schema_verification import validate_existing_data
from app.repositories import ProductRepository
from app.schemas.product import ProductUpdate
from sqlalchemy import create_engine, text


def test_hidden_product_stays_active_but_is_excluded_from_kasse_query(db_session):
    visible = Product(name="Sichtbar", price_cents=100, stock_quantity=5)
    hidden = Product(
        name="Ausgeblendet",
        price_cents=200,
        stock_quantity=8,
        is_visible_in_kasse=False,
    )
    db_session.add_all([visible, hidden])
    db_session.commit()

    repository = ProductRepository(db_session)

    assert {product.name for product in repository.get_all()} == {"Sichtbar", "Ausgeblendet"}
    assert [product.name for product in repository.get_all(only_visible_in_kasse=True)] == ["Sichtbar"]
    assert repository.get_by_id(hidden.id).is_active is True
    assert repository.get_by_id(hidden.id).stock_quantity == 8


def test_product_visibility_cannot_be_set_to_null():
    try:
        ProductUpdate.model_validate({"is_visible_in_kasse": None})
    except ValueError:
        pass
    else:
        raise AssertionError("is_visible_in_kasse=None must be rejected")


def test_validate_existing_data_tolerates_legacy_products_without_kasse_visibility():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                description VARCHAR(255),
                warengruppe VARCHAR(120),
                price_cents INTEGER NOT NULL,
                member_price_cents INTEGER,
                is_discountable BOOLEAN NOT NULL DEFAULT 1,
                stock_quantity INTEGER NOT NULL DEFAULT 0,
                minimum_stock_quantity INTEGER NOT NULL DEFAULT 0,
                notify_on_low_stock BOOLEAN NOT NULL DEFAULT 0,
                is_unlimited_stock BOOLEAN NOT NULL DEFAULT 0,
                is_variable_price BOOLEAN NOT NULL DEFAULT 0,
                image_path VARCHAR(255),
                is_active BOOLEAN NOT NULL DEFAULT 1,
                requires_guest_list BOOLEAN NOT NULL DEFAULT 0,
                opens_small_parts_drawer BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE members (
                id INTEGER PRIMARY KEY,
                archived_at DATETIME,
                member_number INTEGER NOT NULL,
                name VARCHAR(120) NOT NULL,
                first_name VARCHAR(80) NOT NULL,
                last_name VARCHAR(80) NOT NULL,
                membership_number VARCHAR(50),
                email VARCHAR(120),
                phone VARCHAR(20),
                has_discount BOOLEAN NOT NULL DEFAULT 1,
                role VARCHAR(20),
                balance_cents INTEGER NOT NULL DEFAULT 0,
                photo_path VARCHAR(255),
                notes TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                description VARCHAR(255),
                color VARCHAR(20),
                is_active_in_kasse BOOLEAN NOT NULL DEFAULT 1,
                display_order INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """))

    validate_existing_data(engine)
