from app.models import Product
from app.repositories import ProductRepository
from app.schemas.product import ProductUpdate


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
