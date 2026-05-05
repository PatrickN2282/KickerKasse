from fastapi import APIRouter, HTTPException, Depends, Request, status, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core import get_db
from app.core.auth import require_roles
from app.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductStockCorrectionRequest,
    ProductStockCorrectionLogResponse,
)
from app.services import ProductService
from app.services.file_service import save_product_image, save_product_original_image, get_full_path, get_product_original_image_path
from app.repositories import ProductRepository, UserRepository
from app.models import UserRole

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new product"""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    try:
        service = ProductService(db)
        product = service.create_product(
            product_data.name,
            product_data.price_cents,
            product_data.description,
            product_data.member_price_cents,
            product_data.is_discountable,
            product_data.stock_quantity,
            product_data.is_unlimited_stock,
            product_data.warengruppe,
            product_data.is_variable_price,
        )
        return product
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daten ungültig oder dupliziert",
        )


@router.get("/stock-corrections", response_model=list[ProductStockCorrectionLogResponse])
@router.get("/stock-corrections/", response_model=list[ProductStockCorrectionLogResponse])
async def list_stock_corrections(
    request: Request,
    db: Session = Depends(get_db),
):
    """List product stock correction logs."""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    service = ProductService(db)
    return service.get_stock_correction_logs()


@router.get("/", response_model=list[ProductResponse])
@router.get("", response_model=list[ProductResponse])
async def get_products(
    request: Request,
    only_active: bool = True,
    db: Session = Depends(get_db),
):
    """Get all products"""
    if not request.session.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    service = ProductService(db)
    return service.get_all_products(only_active)


@router.get("/{product_id}", response_model=ProductResponse)
@router.get("/{product_id}/", response_model=ProductResponse)
async def get_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get product by ID"""
    if not request.session.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    service = ProductService(db)
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
@router.put("/{product_id}/", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update product"""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    try:
        service = ProductService(db)
        update_dict = product_data.dict(exclude_unset=True)
        product = service.update_product(product_id, **update_dict)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        
        return product
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daten ungültig oder dupliziert",
        )


@router.post("/{product_id}/adjust-stock")
@router.post("/{product_id}/adjust-stock/")
async def adjust_stock(
    product_id: int,
    quantity: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Adjust product stock"""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    service = ProductService(db)
    product = service.adjust_stock(product_id, quantity)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or insufficient stock",
        )
    
    return product


@router.post("/{product_id}/stock-correction", response_model=ProductResponse)
@router.post("/{product_id}/stock-correction/", response_model=ProductResponse)
async def correct_stock(
    product_id: int,
    correction_request: ProductStockCorrectionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Correct product stock without cash flow."""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)

    try:
        service = ProductService(db)
        product = service.correct_stock(
            product_id,
            correction_request.new_stock_quantity,
            current_user.username,
            correction_request.reason,
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return product
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stock correction failed: {str(e)}",
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{product_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete product (soft delete)"""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    service = ProductService(db)
    if not service.delete_product(product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )


@router.post("/{product_id}/image")
@router.post("/{product_id}/image/")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Upload product image"""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    # Check if product exists
    product_repo = ProductRepository(db)
    product = product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
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
    image_path = await save_product_image(file, product_id)
    
    # Update product with image path
    product.image_path = image_path
    db.commit()
    db.refresh(product)
    
    return {"status": "success", "product_id": product_id, "image_path": image_path}


@router.get("/{product_id}/image")
@router.get("/{product_id}/image/")
async def get_product_image(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Get product image file"""
    product_repo = ProductRepository(db)
    product = product_repo.get_by_id(product_id)
    if not product or not product.image_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product or image not found",
        )
    
    # Get full file path
    file_path = get_full_path(product.image_path)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found",
        )
    
    return FileResponse(file_path, media_type="image/jpeg")


@router.post("/{product_id}/original-image")
@router.post("/{product_id}/original-image/")
async def upload_product_original_image(
    product_id: int,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Upload original (uncropped) product image for reset purposes"""
    require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)

    product_repo = ProductRepository(db)
    product = product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    image_data = await file.read()
    if not image_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )
    if len(image_data) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 10MB)",
        )

    await file.seek(0)
    await save_product_original_image(file, product_id)
    return {"status": "success", "product_id": product_id}


@router.get("/{product_id}/original-image")
@router.get("/{product_id}/original-image/")
async def get_product_original_image(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Get original (uncropped) product image"""
    file_path = get_product_original_image_path(product_id)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original image not found",
        )
    return FileResponse(file_path, media_type="image/jpeg")


@router.post("/{product_id}/categories")
@router.post("/{product_id}/categories/")
async def add_category_to_product(
    product_id: int,
    category_ids: list[int],
    request: Request,
    db: Session = Depends(get_db),
):
    """Add categories to a product (admin only)"""
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
            detail="Insufficient permissions",
        )
    
    product_repo = ProductRepository(db)
    product = product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    
    # Import Category here to avoid circular imports
    from app.models import Category
    
    # Get all categories by IDs
    try:
        for category_id in category_ids:
            category = db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category {category_id} not found",
                )
            if category not in product.categories:
                product.categories.append(category)
        
        db.commit()
        db.refresh(product)
        return product
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{product_id}/categories/{category_id}")
@router.delete("/{product_id}/categories/{category_id}/")
async def remove_category_from_product(
    product_id: int,
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Remove a category from a product (admin only)"""
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
            detail="Insufficient permissions",
        )
    
    product_repo = ProductRepository(db)
    product = product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    
    # Import Category here to avoid circular imports
    from app.models import Category
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    if category in product.categories:
        product.categories.remove(category)
        db.commit()
    
    return {"status": "success"}
