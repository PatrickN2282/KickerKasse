from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.core import get_db
from app.schemas import TransactionCreate, TransactionResponse, TransactionStornoCreate, ZBonResponse
from app.services import TransactionService, ProductService
from app.repositories import MemberRepository, ProductRepository
from app.models import PaymentMethod

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("/next-receipt-number")
async def get_next_receipt_number(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get the next receipt number"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    service = TransactionService(db)
    next_number = service.get_next_receipt_number()
    return {"receipt_number": next_number}


@router.post("/sale", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    transaction_data: TransactionCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a sale transaction"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    print(f"[API] Creating sale transaction for user {user_id}: payment_method={transaction_data.payment_method}, member_id={transaction_data.member_id}, items={len(transaction_data.items)}")
    
    # Validate items exist and have stock
    product_repo = ProductRepository(db)
    for item in transaction_data.items:
        product = product_repo.get_by_id(item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found",
            )
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unzureichender Bestand für Produkt {product.name}",
            )
    
    # Check member balance if paying with balance
    if transaction_data.payment_method == "BALANCE":
        if not transaction_data.member_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Member ID required for balance payment",
            )
        
        member_repo = MemberRepository(db)
        member = member_repo.get_by_id(transaction_data.member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )
        
        # Calculate total amount
        total_amount = 0
        for item in transaction_data.items:
            total_amount += item.unit_price_cents * item.quantity
        
        if member.balance_cents < total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient member balance",
            )
    
    service = TransactionService(db)
    
    # Calculate total amount
    total_amount = sum(item.unit_price_cents * item.quantity for item in transaction_data.items)
    
    # Create transaction
    items_data = [item.dict() for item in transaction_data.items]
    transaction = service.create_sale_transaction(
        user_id=user_id,
        total_amount_cents=total_amount,
        payment_method=transaction_data.payment_method,
        member_id=transaction_data.member_id,
        items=items_data,
    )
    
    # Process payment
    member_repo = MemberRepository(db)
    service.process_sale_payment(transaction, member_repo)
    
    # Deduct stock for each item
    for item in transaction.items:
        product_repo.deduct_stock(item.product_id, item.quantity)
    
    # Final commit to ensure everything is persisted
    db.commit()
    db.refresh(transaction)
    
    print(f"[API] Sale transaction created successfully: id={transaction.id}, receipt_number={transaction.receipt_number}, amount={total_amount}")
    
    return transaction


@router.post("/storno", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_storno(
    storno_data: TransactionStornoCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a storno (reversal) transaction"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    service = TransactionService(db)
    
    try:
        storno = service.create_storno_transaction(
            storno_data.transaction_id,
            user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Process storno payment
    member_repo = MemberRepository(db)
    service.process_storno_payment(storno, member_repo)
    
    # Add back stock for each item
    product_repo = ProductRepository(db)
    for item in storno.reference_transaction.items:
        product_repo.add_stock(item.product_id, item.quantity)
    
    return storno


@router.get("/daily-summary")
async def get_daily_summary(
    date_param: str,  # format: YYYY-MM-DD
    request: Request,
    password: str = None,
    db: Session = Depends(get_db),
):
    """Get daily summary (Z-Bon) - requires password"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # Password check (should be passed as query or body)
    # For now, just check if user is authenticated
    # In production, add additional password protection
    
    try:
        summary_date = datetime.strptime(date_param, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )
    
    service = TransactionService(db)
    summary = service.get_daily_summary(summary_date)
    
    return ZBonResponse(
        total_cash_cents=summary["total_cash_cents"],
        total_balance_cents=summary["total_balance_cents"],
        transaction_count=summary["transaction_count"],
        created_at=datetime.now(),
    )


@router.get("/daily-stats")
async def get_daily_stats(
    date: str,  # format: YYYY-MM-DD
    request: Request,
    db: Session = Depends(get_db),
):
    """Get daily statistics with transaction list"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    try:
        summary_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )
    
    service = TransactionService(db)
    stats = service.get_daily_stats(summary_date)
    
    return stats


@router.get("/filtered")
async def get_filtered_transactions(
    start_date: str,
    end_date: str,
    request: Request,
    payment_method: str = None,
    db: Session = Depends(get_db),
):
    """Get filtered transactions"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD",
        )
    
    service = TransactionService(db)
    result = service.get_filtered_transactions(start, end, payment_method)
    
    return result


@router.get("/revenue-stats")
async def get_revenue_stats(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get revenue statistics"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    try:
        service = TransactionService(db)
        stats = service.get_revenue_stats()
        print(f"[API] Revenue stats loaded: {stats}")
        return stats
    except Exception as e:
        print(f"[API] Error loading revenue stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading revenue stats: {str(e)}",
        )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get transaction by ID"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    service = TransactionService(db)
    transaction = service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    
    return transaction


@router.get("/", response_model=list[TransactionResponse])
async def get_transactions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all transactions"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    service = TransactionService(db)
    return service.get_all_transactions(skip, limit)
