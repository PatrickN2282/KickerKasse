from app.core.booking_route import BookingRoute
from pydantic import BaseModel, Field, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_authenticated_user
from app.services import DeckelService, MaterialAccountService, TransactionService
from app.repositories import ProductRepository
from app.utils.drawer import SMALL_PARTS_DRAWER, drawer_targets_for_sale, requires_small_parts_drawer

router = APIRouter(route_class=BookingRoute, prefix="/api/deckel", tags=["Deckel"])


class DeckelItemPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: int
    quantity: int = Field(..., ge=1)
    unit_price_cents: int = Field(..., ge=0)
    is_internal_material: bool = False
    note: str | None = Field(default=None, max_length=500)


class DeckelCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=120)
    items: list[DeckelItemPayload] = Field(default_factory=list)


class DeckelBookPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[DeckelItemPayload] = Field(default_factory=list)


class DeckelPaymentPayload(BaseModel):
    cash_received_cents: int = Field(..., ge=0)
    tip_cents: int = Field(default=0, ge=0)


def _serialize_deckel(deckel) -> dict:
    items = [
        {
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else f"Produkt {item.product_id}",
            "quantity": item.quantity,
            "unit_price_cents": item.unit_price_cents,
            "total_price_cents": item.total_price_cents,
            "is_internal_material": item.is_internal_material,
            "note": item.note,
        }
        for item in deckel.items
    ]
    return {
        "id": deckel.id,
        "name": deckel.name,
        "created_at": deckel.created_at,
        "updated_at": deckel.updated_at,
        "total_amount_cents": sum(item["total_price_cents"] for item in items),
        "items": items,
    }


def _drawer_targets_for_booked_items(db: Session, items: list[DeckelItemPayload]) -> list[str]:
    product_repo = ProductRepository(db)
    products = [product_repo.get_by_id(item.product_id) for item in items]
    return [SMALL_PARTS_DRAWER] if requires_small_parts_drawer(
        product for product in products if product is not None
    ) else []


@router.get("/")
@router.get("")
async def list_deckel(
    request: Request,
    db: Session = Depends(get_db),
):
    require_authenticated_user(request, db)
    service = DeckelService(db)
    return [_serialize_deckel(deckel) for deckel in service.list_deckel()]


@router.post("/", status_code=status.HTTP_201_CREATED)
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_deckel(
    payload: DeckelCreatePayload,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_authenticated_user(request, db)
    try:
        deckel = DeckelService(db).create_deckel(
            payload.name,
            user.id,
            [item.model_dump() for item in payload.items],
        )
        result = _serialize_deckel(deckel)
        result["drawer_targets"] = _drawer_targets_for_booked_items(db, payload.items)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{deckel_id}")
@router.get("/{deckel_id}/")
async def get_deckel(
    deckel_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    require_authenticated_user(request, db)
    deckel = DeckelService(db).get_deckel(deckel_id)
    if not deckel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deckel nicht gefunden")

    return _serialize_deckel(deckel)


@router.post("/{deckel_id}/book")
@router.post("/{deckel_id}/book/")
async def book_to_deckel(
    deckel_id: int,
    payload: DeckelBookPayload,
    request: Request,
    db: Session = Depends(get_db),
):
    require_authenticated_user(request, db)
    try:
        deckel = DeckelService(db).append_items(
            deckel_id,
            [item.model_dump() for item in payload.items],
        )
        result = _serialize_deckel(deckel)
        result["drawer_targets"] = _drawer_targets_for_booked_items(db, payload.items)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{deckel_id}/pay", status_code=status.HTTP_201_CREATED)
@router.post("/{deckel_id}/pay/", status_code=status.HTTP_201_CREATED)
async def pay_deckel(
    deckel_id: int,
    payload: DeckelPaymentPayload,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_authenticated_user(request, db)
    try:
        transaction = DeckelService(db).settle(deckel_id, user, payload.cash_received_cents, payload.tip_cents)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Stock items have already been physically issued when they were booked to
    # the Deckel. Settlement therefore opens only the cash drawer.
    drawer_targets = drawer_targets_for_sale(
        [],
        transaction.payment_method,
        transaction.total_amount_cents,
        transaction.tip_cents,
        transaction.cash_received_cents,
        transaction.change_given_cents,
    )

    return {
        "id": transaction.id,
        "receipt_number": transaction.receipt_number,
        "type": transaction.type.value,
        "payment_method": transaction.payment_method.value,
        "total_amount_cents": transaction.total_amount_cents,
        "user_id": transaction.user_id,
        "member_id": transaction.member_id,
        "voucher_code": transaction.voucher_code,
        "voucher_type": transaction.voucher_type,
        "voucher_applied_cents": transaction.voucher_applied_cents or 0,
        "balance_applied_cents": transaction.balance_applied_cents or 0,
        "tip_cents": transaction.tip_cents or 0,
        "cash_received_cents": transaction.cash_received_cents,
        "change_given_cents": transaction.change_given_cents,
        "open_small_parts_drawer": False,
        "drawer_targets": drawer_targets,
        "items": transaction.items,
        "issued_prepaid_voucher_numbers": [],
        "next_unissued_prepaid_voucher_number": None,
        "created_at": transaction.created_at,
        "updated_at": transaction.updated_at,
    }
