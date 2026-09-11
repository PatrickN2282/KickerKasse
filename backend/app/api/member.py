from app.core.atomic import audited_media
from app.core.booking_route import BookingRoute
from app.core.auth import require_session
from fastapi import APIRouter, HTTPException, Depends, Request, status, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from app.schemas.validation import MAX_INT
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core import get_db
from app.core.auth import require_authenticated_user, require_password_confirmation, require_roles
from app.schemas.member import MemberSelectionResponse
from app.schemas import (
    MemberCreate,
    MemberUpdate,
    MemberResponse,
    MemberRechargeResponse,
    MemberBalanceCorrectionRequest,
    MemberBalanceCorrectionLogResponse,
)
from app.services import MemberService
from app.services.audit_log_service import AuditLogService
from app.services.file_service import (
    save_member_photo,
    save_member_original_photo,
    get_full_path,
    get_member_original_photo_path,
    get_media_type,
    delete_member_photo,
)
from app.repositories import MemberRepository, UserRepository
from app.models import UserRole

router = APIRouter(route_class=BookingRoute, prefix="/api/members", tags=["Members"])
MAX_PHOTO_SIZE_BYTES = 5 * 1024 * 1024


class MemberRechargeRequest(BaseModel):
    amount_cents: int = Field(..., gt=0, le=MAX_INT)
    auth_password: str


@router.get("/balance-corrections", response_model=list[MemberBalanceCorrectionLogResponse])
@router.get("/balance-corrections/", response_model=list[MemberBalanceCorrectionLogResponse])
async def list_balance_corrections(
    request: Request,
    db: Session = Depends(get_db),
):
    """List member balance correction logs."""
    require_roles(request, db, UserRole.ADMIN)
    service = MemberService(db)
    return service.get_balance_correction_logs()


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(
    member_data: MemberCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new member"""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    if member_data.role and not current_user.is_top_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur der Top-Admin darf Rollen vergeben",
        )
    
    try:
        service = MemberService(db)
        member = service.create_member(
            member_data.first_name,
            member_data.last_name,
            member_data.membership_number,
            member_data.email,
            member_data.phone,
            member_data.notes,
            member_data.has_discount,
            member_data.role,
            member_data.account_password,
            performed_by_username=current_user.username,
        )
        return member
    except IntegrityError as e:
        db.rollback()
        if "email" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Diese E-Mail-Adresse existiert bereits",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daten ungültig oder dupliziert",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/selection", response_model=list[MemberSelectionResponse])
@router.get("/selection/", response_model=list[MemberSelectionResponse])
async def get_member_selection(request: Request, db: Session = Depends(get_db)):
    require_authenticated_user(request, db)
    return MemberService(db).get_all_members()


@router.get("/", response_model=list[MemberResponse])
@router.get("", response_model=list[MemberResponse])
async def get_members(
    request: Request,
    include_archived: bool = False,
    db: Session = Depends(get_db),
):
    """Get all members"""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    service = MemberService(db)
    return service.get_all_members(include_archived=include_archived)


@router.get("/statistics")
@router.get("/statistics/")
async def get_member_statistics(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get member statistics"""
    require_roles(request, db, UserRole.ADMIN)
    
    try:
        from datetime import date, timedelta
        from sqlalchemy import func
        from app.models import Transaction, TransactionType, Member
        
        member_repo = MemberRepository(db)
        all_members = member_repo.get_all()
        
        # Total balance
        total_balance = sum(m.balance_cents for m in all_members)
        
        # Active members this week
        week_ago = date.today() - timedelta(days=7)
        active_members = db.query(func.count(func.distinct(Transaction.member_id))).filter(
            func.date(Transaction.created_at) >= week_ago,
            Transaction.type == TransactionType.SALE,
            Transaction.member_id != None
        ).scalar() or 0
        
        # Top members by spending
        top_members_query = db.query(
            Member.id,
            Member.name,
            Member.balance_cents,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.total_amount_cents).label('total_spent'),
        ).join(
            Transaction, Member.id == Transaction.member_id
        ).filter(
            Transaction.type == TransactionType.SALE
        ).group_by(
            Member.id, Member.name, Member.balance_cents
        ).order_by(
            func.sum(Transaction.total_amount_cents).desc()
        ).limit(10).all()
        
        result = {
            "total_members": len(all_members),
            "active_this_week": active_members,
            "total_balance": total_balance,
            "top_members": [
                {
                    "id": m[0],
                    "name": m[1],
                    "balance_cents": m[2],
                    "transaction_count": m[3] or 0,
                    "total_spent": m[4] or 0,
                }
                for m in top_members_query
            ],
        }
        
        print(f"[API] Member statistics loaded: {result}")
        return result
    except Exception as e:
        print(f"[API] Error loading member statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading member statistics: {str(e)}",
        )


@router.get("/{member_id}", response_model=MemberResponse)
@router.get("/{member_id}/", response_model=MemberResponse)
async def get_member(
    member_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get member by ID"""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    service = MemberService(db)
    member = service.get_member(member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    
    return member


@router.put("/{member_id}", response_model=MemberResponse)
@router.put("/{member_id}/", response_model=MemberResponse)
async def update_member(
    member_id: int,
    member_data: MemberUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update member"""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    if member_data.account_password is not None and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Admin oder Top-Admin dürfen Passwörter neu vergeben",
        )
    if "role" in member_data.model_fields_set and not current_user.is_top_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur der Top-Admin darf Rollen vergeben",
        )

    if member_data.account_password is not None and not current_user.is_top_admin:
        if UserRepository(db).get_by_member_id(member_id) is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur der Top-Admin darf einen Mitgliedszugang erstmalig einrichten",
            )
    
    try:
        service = MemberService(db)
        update_dict = member_data.model_dump(exclude_unset=True)
        account_password = update_dict.pop("account_password", None)
        member = service.update_member(member_id, account_password=account_password, performed_by_username=current_user.username, **update_dict)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )
        
        return member
    except IntegrityError as e:
        db.rollback()
        if "email" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Diese E-Mail-Adresse existiert bereits",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daten ungültig oder dupliziert",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{member_id}/recharge", response_model=MemberRechargeResponse)
@router.post("/{member_id}/recharge/", response_model=MemberRechargeResponse)
async def recharge_member_balance(
    member_id: int,
    recharge_request: MemberRechargeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Recharge member balance"""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    user_id = current_user.id
    require_password_confirmation(current_user, recharge_request.auth_password, db)
    
    try:
        member = MemberService(db).recharge_balance(
            member_id, recharge_request.amount_cents, "RECHARGE", current_user.username,
            executed_by_user_id=user_id,
        )
        if not member:
            raise HTTPException(status_code=404, detail="Mitglied nicht gefunden")
        member.drawer_targets = ["main"]
        return member
    except HTTPException:
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Aufladung konnte nicht bestätigt werden. Bitte Guthaben und Historie prüfen, bevor du erneut auflädst.") from exc


@router.post("/{member_id}/balance-correction", response_model=MemberResponse)
@router.post("/{member_id}/balance-correction/", response_model=MemberResponse)
async def correct_member_balance(
    member_id: int,
    correction_request: MemberBalanceCorrectionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Correct member balance without cash flow."""
    current_user = require_roles(request, db, UserRole.ADMIN)

    try:
        service = MemberService(db)
        member = service.correct_balance(
            member_id,
            correction_request.new_balance_cents,
            executed_by_user_id=current_user.id,
            executed_by_username=current_user.username,
            reason=correction_request.reason,
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )
        return member
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Balance correction failed: {str(e)}",
        )


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{member_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    member_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete member"""
    current_user = require_roles(request, db, UserRole.ADMIN)

    target = MemberService(db).get_member(member_id)
    if target and (target.role is not None or target.linked_user is not None) and not current_user.is_top_admin:
        raise HTTPException(403, "Mitglieder mit Systemzugang darf nur der Top-Admin archivieren.")
    try:
        if not MemberService(db).delete_member(member_id, performed_by_username=current_user.username):
            raise HTTPException(404, "Mitglied nicht gefunden")
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/{member_id}/restore", status_code=204)
async def restore_member(member_id: int, request: Request, db: Session = Depends(get_db)):
    actor = require_roles(request, db, UserRole.ADMIN)
    target = MemberService(db).get_member(member_id)
    if target and (target.role is not None or target.linked_user is not None) and not actor.is_top_admin:
        raise HTTPException(403, "Mitglieder mit Systemzugang darf nur der Top-Admin wiederherstellen.")
    try:
        if not MemberService(db).set_archived(member_id, False, actor.username):
            raise HTTPException(404, "Mitglied nicht gefunden")
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/{member_id}/photo")
@router.post("/{member_id}/photo/")
@audited_media("members", "member_id")
async def upload_member_photo(
    member_id: int,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Upload member photo"""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    # Check if member exists
    member_repo = MemberRepository(db)
    member = member_repo.get_by_id(member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    
    # Read image data to check size
    image_data = await file.read()
    if not image_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )
    
    # Limit file size to 5MB
    if len(image_data) > MAX_PHOTO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 5MB)",
        )
    
    # Reset file pointer and save to disk
    await file.seek(0)
    photo_path = await save_member_photo(file, member_id)
    
    # Update member with photo path
    member.photo_path = photo_path

    AuditLogService(db).log(
        entity_type="member",
        action="IMAGE_UPDATED",
        user_username=current_user.username,
        entity_id=member_id,
        entity_name=member.name,
        new_value={"photo_path": photo_path},
    )

    db.commit()
    db.refresh(member)
    
    return {"status": "success", "member_id": member_id, "photo_path": photo_path}


@router.post("/{member_id}/original-photo")
@router.post("/{member_id}/original-photo/")
@audited_media("members", "member_id")
async def upload_member_original_photo(
    member_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)

    member_repo = MemberRepository(db)
    member = member_repo.get_by_id(member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    image_data = await file.read()
    if not image_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    if len(image_data) > MAX_PHOTO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 5MB)",
        )

    await file.seek(0)
    await save_member_original_photo(file, member_id)
    AuditLogService(db).log(entity_type="member", action="ORIGINAL_IMAGE_UPDATED",
        user_username=current_user.username, entity_id=member_id, entity_name=member.name)
    return {"status": "success", "member_id": member_id}


@router.delete("/{member_id}/photo")
@router.delete("/{member_id}/photo/")
@audited_media("members", "member_id")
async def delete_member_photo_file(
    member_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete member photo and reset stored photo path."""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)

    member_repo = MemberRepository(db)
    member = member_repo.get_by_id(member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    delete_member_photo(member_id)
    member.photo_path = None
    db.commit()
    db.refresh(member)

    AuditLogService(db).log(entity_type="member", action="IMAGE_DELETED",
        user_username=current_user.username, entity_id=member_id, entity_name=member.name)
    return {"status": "success", "member_id": member_id}


@router.get("/{member_id}/photo", dependencies=[Depends(require_session)])
@router.get("/{member_id}/photo/", dependencies=[Depends(require_session)])
async def get_member_photo(
    member_id: int,
    db: Session = Depends(get_db),
):
    """Get member photo file"""
    member_repo = MemberRepository(db)
    member = member_repo.get_by_id(member_id)
    if not member or not member.photo_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member or photo not found",
        )
    
    # Get full file path
    file_path = get_full_path(member.photo_path)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo file not found",
        )
    
    return FileResponse(file_path, media_type=get_media_type(file_path))


@router.get("/{member_id}/original-photo", dependencies=[Depends(require_session)])
@router.get("/{member_id}/original-photo/", dependencies=[Depends(require_session)])
async def get_member_original_photo(
    member_id: int,
    db: Session = Depends(get_db),
):
    member_repo = MemberRepository(db)
    member = member_repo.get_by_id(member_id)
    if not member or not member.photo_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member or photo not found",
        )

    file_path = get_member_original_photo_path(member_id)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original photo not found",
        )

    return FileResponse(file_path, media_type=get_media_type(file_path))
