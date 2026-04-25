from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.auth import require_authenticated_user
from app.services import DeckelService, MaterialAccountService, TransactionService
from app.repositories import ProductRepository

router = APIRouter(prefix="/api/deckel", tags=["Deckel"])


class DeckelItemPayload(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
    unit_price_cents: int = Field(..., ge=0)
    is_internal_material: bool = False


class DeckelCreatePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    items: list[DeckelItemPayload] = Field(default_factory=list)


class DeckelBookPayload(BaseModel):
    items: list[DeckelItemPayload] = Field(default_factory=list)


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
        return _serialize_deckel(deckel)
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
        return _serialize_deckel(deckel)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{deckel_id}/pay", status_code=status.HTTP_201_CREATED)
@router.post("/{deckel_id}/pay/", status_code=status.HTTP_201_CREATED)
async def pay_deckel(
    deckel_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_authenticated_user(request, db)
    deckel_service = DeckelService(db)
    deckel = deckel_service.get_deckel(deckel_id)
    if not deckel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deckel nicht gefunden")

    items_payload = [
        {
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price_cents": item.unit_price_cents,
            "is_internal_material": item.is_internal_material,
        }
        for item in deckel.items
    ]

    try:
        deckel_service.validate_item_stock(items_payload, exclude_deckel_id=deckel.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    transaction_service = TransactionService(db)
    transaction = transaction_service.create_sale_transaction(
        user_id=user.id,
        total_amount_cents=sum(item["quantity"] * item["unit_price_cents"] for item in items_payload),
        payment_method="CASH",
        items=items_payload,
    )

    product_repo = ProductRepository(db)
    for item in transaction.items:
        product_repo.deduct_stock(item.product_id, item.quantity)

    MaterialAccountService(db).record_sale_transaction(transaction)
    deckel_service.delete_deckel(deckel.id)
    db.refresh(transaction)

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
        "items": transaction.items,
        "issued_prepaid_voucher_numbers": [],
        "next_unissued_prepaid_voucher_number": None,
        "created_at": transaction.created_at,
        "updated_at": transaction.updated_at,
    }
