from app.core.auth import require_authenticated_user, require_roles
from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import String, cast, desc, or_
from typing import List, Optional
from datetime import datetime, time

from app.core import get_db
from app.core.auth import require_authenticated_user
from app.models import GuestListEntry, Member, Transaction, UserRole
from app.models.product import Product
from app.schemas.guest_list import (
    GuestListEntryCreate,
    GuestListEntryBatchCreate,
    GuestListEntryResponse,
    GuestListByProductResponse,
    GuestListPageResponse,
    GuestListProductResponse,
    KnownGuestResponse,
)

router = APIRouter(prefix="/api/guest-list", tags=["Guest List"])


def _normalize_guest_name_parts(
    guest_name: str | None,
    guest_first_name: str | None,
    guest_last_name: str | None,
) -> tuple[str, str | None, str]:
    first_name = (guest_first_name or "").strip()
    last_name = (guest_last_name or "").strip()
    full_name = (guest_name or "").strip()

    if not first_name and full_name:
        parts = full_name.split(maxsplit=1)
        first_name = parts[0]
        if len(parts) > 1 and not last_name:
            last_name = parts[1]

    normalized_full_name = f"{first_name} {last_name}".strip() if first_name else full_name
    return first_name, (last_name or None), normalized_full_name


def _build_short_display_name(first_name: str, last_name: str | None) -> str:
    normalized_last_name = (last_name or "").strip()
    if not normalized_last_name:
        return first_name
    return f"{first_name} {normalized_last_name[:1]}."


def _entry_to_response(entry: GuestListEntry) -> GuestListEntryResponse:
    guest_first_name, guest_last_name, guest_name = _normalize_guest_name_parts(
        entry.guest_name,
        entry.guest_first_name,
        entry.guest_last_name,
    )
    return GuestListEntryResponse(
        id=entry.id,
        product_id=entry.product_id,
        product_name=entry.product.name if entry.product else "",
        member_id=entry.member_id,
        member_name=entry.member.name if entry.member else None,
        guest_name=guest_name,
        guest_first_name=guest_first_name,
        guest_last_name=guest_last_name,
        transaction_id=entry.transaction_id,
        transaction_item_id=entry.transaction_item_id,
        receipt_number=entry.transaction.receipt_number if entry.transaction else None,
        created_at=entry.created_at,
    )


@router.post("/entries", response_model=List[GuestListEntryResponse], status_code=status.HTTP_201_CREATED)
@router.post("/entries/", response_model=List[GuestListEntryResponse], status_code=status.HTTP_201_CREATED)
async def create_guest_list_entries(
    batch: GuestListEntryBatchCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create one or more guest list entries."""
    require_authenticated_user(request, db)

    raise HTTPException(status_code=409, detail="Gäste werden gemeinsam mit dem Verkauf gespeichert. Bitte die Kasse aktualisieren.")


@router.get("/entries", response_model=List[GuestListByProductResponse])
@router.get("/entries/", response_model=List[GuestListByProductResponse])
async def list_guest_list_entries(
    request: Request,
    product_id: Optional[int] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List guest list entries grouped by product."""
    require_authenticated_user(request, db)

    query = (
        db.query(GuestListEntry)
        .join(Product, GuestListEntry.product_id == Product.id)
        .options(
            joinedload(GuestListEntry.product),
            joinedload(GuestListEntry.member),
            joinedload(GuestListEntry.transaction),
        )
        .order_by(desc(GuestListEntry.created_at))
    )

    if product_id is not None:
        query = query.filter(GuestListEntry.product_id == product_id)

    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Expected format: YYYY-MM-DD",
            ) from exc
        start_dt = datetime.combine(target_date, time.min)
        end_dt = datetime.combine(target_date, time.max)
        query = query.filter(GuestListEntry.created_at >= start_dt, GuestListEntry.created_at <= end_dt)

    entries = query.all()

    # Group by product
    product_map: dict[int, dict] = {}
    for entry in entries:
        pid = entry.product_id
        if pid not in product_map:
            product_map[pid] = {
                "product_id": pid,
                "product_name": entry.product.name if entry.product else "",
                "entries": [],
            }
        product_map[pid]["entries"].append(_entry_to_response(entry))

    return [GuestListByProductResponse(**v) for v in product_map.values()]


@router.get("/entries-page", response_model=GuestListPageResponse)
@router.get("/entries-page/", response_model=GuestListPageResponse)
async def list_guest_list_entries_page(
    request: Request,
    product_id: Optional[int] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    """Return one filtered guest-list page without transferring the full history."""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    query = db.query(GuestListEntry).join(Product).options(
        joinedload(GuestListEntry.product),
        joinedload(GuestListEntry.member),
        joinedload(GuestListEntry.transaction),
    )
    if product_id is not None:
        query = query.filter(GuestListEntry.product_id == product_id)
    if date_from is not None:
        query = query.filter(GuestListEntry.created_at >= date_from)
    if date_to is not None:
        query = query.filter(GuestListEntry.created_at <= date_to)
    normalized_search = (search or "").strip()
    if normalized_search:
        pattern = f"%{normalized_search}%"
        query = query.filter(or_(
            GuestListEntry.guest_name.ilike(pattern),
            GuestListEntry.guest_first_name.ilike(pattern),
            GuestListEntry.guest_last_name.ilike(pattern),
            Product.name.ilike(pattern),
            GuestListEntry.member.has(Member.name.ilike(pattern)),
            GuestListEntry.transaction.has(cast(Transaction.receipt_number, String).ilike(pattern)),
        ))
    total = query.count()
    entries = query.order_by(desc(GuestListEntry.created_at), desc(GuestListEntry.id)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return GuestListPageResponse(
        entries=[_entry_to_response(entry) for entry in entries],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/products", response_model=List[GuestListProductResponse])
@router.get("/products/", response_model=List[GuestListProductResponse])
async def list_guest_list_products(request: Request, db: Session = Depends(get_db)):
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    rows = db.query(Product.id, Product.name).join(GuestListEntry).distinct().order_by(Product.name).all()
    return [GuestListProductResponse(id=row.id, name=row.name) for row in rows]


@router.get("/guests", response_model=List[KnownGuestResponse])
@router.get("/guests/", response_model=List[KnownGuestResponse])
async def list_known_guests(
    request: Request,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Return distinct guest names for autocomplete dropdown."""
    require_authenticated_user(request, db)

    query = db.query(
        GuestListEntry.guest_name,
        GuestListEntry.guest_first_name,
        GuestListEntry.guest_last_name,
        GuestListEntry.created_at,
    )
    if product_id is not None:
        query = query.filter(GuestListEntry.product_id == product_id)

    results = query.order_by(desc(GuestListEntry.created_at)).all()

    seen_names: set[tuple[str, str]] = set()
    known_guests: List[KnownGuestResponse] = []
    for row in results:
        guest_first_name, guest_last_name, guest_name = _normalize_guest_name_parts(
            row[0],
            row[1],
            row[2],
        )
        if not guest_first_name:
            continue

        key = (guest_first_name.lower(), (guest_last_name or "").lower())
        if key in seen_names:
            continue
        seen_names.add(key)

        known_guests.append(
            KnownGuestResponse(
                guest_name=guest_name,
                guest_first_name=guest_first_name,
                guest_last_name=guest_last_name,
                short_display_name=_build_short_display_name(guest_first_name, guest_last_name),
            )
        )

    known_guests.sort(key=lambda guest: guest.guest_name.lower())
    return known_guests
