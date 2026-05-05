from fastapi import APIRouter, HTTPException, Depends, Request, status, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core import get_db
from app.core.auth import require_password_confirmation, require_roles
from app.schemas import (
    MemberCreate,
    MemberUpdate,
    MemberResponse,
    MemberBalanceCorrectionRequest,
    MemberBalanceCorrectionLogResponse,
)
from app.services import MemberService
from app.services.file_service import save_member_photo, get_full_path
from app.repositories import MemberRepository, UserRepository
from app.models import UserRole

router = APIRouter(prefix="/api/members", tags=["Members"])


class MemberRechargeRequest(BaseModel):
    amount_cents: int
    auth_password: str


@router.get("/balance-corrections", response_model=list[MemberBalanceCorrectionLogResponse])
@router.get("/balance-corrections/", response_model=list[MemberBalanceCorrectionLogResponse])
async def list_balance_corrections(
    request: Request,
    db: Session = Depends(get_db),
):
    """List member balance correction logs."""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
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


@router.get("/", response_model=list[MemberResponse])
@router.get("", response_model=list[MemberResponse])
async def get_members(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get all members"""
    if not request.session.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    service = MemberService(db)
    return service.get_all_members()


@router.get("/statistics")
@router.get("/statistics/")
async def get_member_statistics(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get member statistics"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    if not request.session.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    if member_data.role is not None and not current_user.is_top_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur der Top-Admin darf Rollen vergeben",
        )
    
    try:
        service = MemberService(db)
        update_dict = member_data.model_dump(exclude_unset=True)
        account_password = update_dict.pop("account_password", None)
        member = service.update_member(member_id, account_password=account_password, **update_dict)
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


@router.post("/{member_id}/recharge")
@router.post("/{member_id}/recharge/")
async def recharge_member_balance(
    member_id: int,
    recharge_request: MemberRechargeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Recharge member balance"""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    user_id = current_user.id
    require_password_confirmation(current_user, recharge_request.auth_password)
    
    if recharge_request.amount_cents <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive",
        )
    
    from app.models import PaymentMethod, TransactionType
    from app.repositories import TransactionRepository
    
    try:
        service = MemberService(db)
        member = service.recharge_balance(member_id, recharge_request.amount_cents, "RECHARGE")
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )
        
        # Create RECHARGE transaction for financial tracking
        transaction_repo = TransactionRepository(db)
        transaction_repo.create(
            type=TransactionType.RECHARGE,
            payment_method=PaymentMethod.CASH,  # Recharge is recorded as cash transaction
            total_amount_cents=recharge_request.amount_cents,
            user_id=user_id,
            member_id=member_id,
            items=[],  # No items for recharge
        )
        
        # Ensure everything is committed
        db.commit()
        
        # Refresh member to get latest balance from DB
        db.refresh(member)
        
        print(f"[API] Member {member_id} recharged with {recharge_request.amount_cents} cents. New balance: {member.balance_cents}")
        
        return member
    except Exception as e:
        print(f"[API] Error during recharge: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recharge failed: {str(e)}",
        )


@router.post("/{member_id}/balance-correction", response_model=MemberResponse)
@router.post("/{member_id}/balance-correction/", response_model=MemberResponse)
async def correct_member_balance(
    member_id: int,
    correction_request: MemberBalanceCorrectionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Correct member balance without cash flow."""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)

    try:
        service = MemberService(db)
        member = service.correct_balance(
            member_id,
            correction_request.new_balance_cents,
            current_user.username,
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
    from app.repositories import UserRepository
    from app.models import UserRole
    
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # Check if admin
    current_user = UserRepository(db).get_by_id(user_id)
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    service = MemberService(db)
    if not service.delete_member(member_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )


@router.post("/{member_id}/photo")
@router.post("/{member_id}/photo/")
async def upload_member_photo(
    member_id: int,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Upload member photo"""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
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
    if len(image_data) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 5MB)",
        )
    
    # Reset file pointer and save to disk
    await file.seek(0)
    photo_path = await save_member_photo(file, member_id)
    
    # Update member with photo path
    member.photo_path = photo_path
    db.commit()
    db.refresh(member)
    
    return {"status": "success", "member_id": member_id, "photo_path": photo_path}


@router.get("/{member_id}/photo")
@router.get("/{member_id}/photo/")
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
    
    return FileResponse(file_path, media_type="image/jpeg")
