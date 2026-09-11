from app.core.atomic import audited_media
from app.core.atomic import audited_change
from app.core.auth import require_session
from app.core.auth import require_authenticated_user, require_roles
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
    ProductMutationResponse,
    ProductStockCorrectionRequest,
    ProductStockCorrectionLogResponse,
)
from app.services import ProductService
from app.services.audit_log_service import AuditLogService
from app.services.file_service import (
    save_product_image,
    save_product_original_image,
    get_full_path,
    get_product_original_image_path,
    get_media_type,
    delete_product_image,
)
from app.repositories import ProductRepository, UserRepository
from app.models import UserRole
from app.utils.drawer import drawer_targets_for_stock_change

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.post("/", response_model=ProductMutationResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=ProductMutationResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new product"""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    try:
        service = ProductService(db)
        product = service.create_product(
            product_data.name,
            product_data.price_cents,
            product_data.description,
            product_data.member_price_cents,
            product_data.is_discountable,
            product_data.stock_quantity,
            product_data.minimum_stock_quantity,
            product_data.notify_on_low_stock,
            product_data.is_unlimited_stock,
            product_data.warengruppe,
            product_data.is_variable_price,
            product_data.is_visible_in_kasse,
            product_data.requires_guest_list,
            product_data.opens_small_parts_drawer,
            performed_by_username=current_user.username,
        )
        product.drawer_targets = drawer_targets_for_stock_change(product, 0, product.stock_quantity)
        return product
    except IntegrityError:
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
    require_roles(request, db, UserRole.ADMIN)
    service = ProductService(db)
    return service.get_stock_correction_logs()


@router.get("/", response_model=list[ProductResponse])
@router.get("", response_model=list[ProductResponse])
async def get_products(
    request: Request,
    only_active: bool = True,
    only_visible_in_kasse: bool = False,
    db: Session = Depends(get_db),
):
    """Get all products"""
    require_authenticated_user(request, db)
    
    service = ProductService(db)
    return service.get_all_products(only_active, only_visible_in_kasse)


@router.get("/{product_id}", response_model=ProductResponse)
@router.get("/{product_id}/", response_model=ProductResponse)
async def get_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get product by ID"""
    require_authenticated_user(request, db)
    
    service = ProductService(db)
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    
    return product


@router.put("/{product_id}", response_model=ProductMutationResponse)
@router.put("/{product_id}/", response_model=ProductMutationResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update product"""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    try:
        service = ProductService(db)
        existing = service.get_product(product_id)
        old_stock_quantity = existing.stock_quantity if existing else 0
        update_dict = product_data.dict(exclude_unset=True)
        product = service.update_product(product_id, performed_by_username=current_user.username, **update_dict)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        
        product.drawer_targets = drawer_targets_for_stock_change(
            product,
            old_stock_quantity,
            product.stock_quantity,
        )
        return product
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
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
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    service = ProductService(db)
    existing = service.get_product(product_id)
    old_stock_quantity = existing.stock_quantity if existing else 0
    try:
        product = service.adjust_stock(product_id, quantity, current_user.username)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or insufficient stock",
        )
    
    product.drawer_targets = drawer_targets_for_stock_change(product, old_stock_quantity, product.stock_quantity)
    return product


@router.post("/{product_id}/stock-correction", response_model=ProductMutationResponse)
@router.post("/{product_id}/stock-correction/", response_model=ProductMutationResponse)
async def correct_stock(
    product_id: int,
    correction_request: ProductStockCorrectionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Correct product stock without cash flow."""
    current_user = require_roles(request, db, UserRole.ADMIN)

    try:
        service = ProductService(db)
        existing = service.get_product(product_id)
        old_stock_quantity = existing.stock_quantity if existing else 0
        product = service.correct_stock(
            product_id,
            correction_request.new_stock_quantity,
            executed_by_user_id=current_user.id,
            executed_by_username=current_user.username,
            reason=correction_request.reason,
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        product.drawer_targets = drawer_targets_for_stock_change(
            product,
            old_stock_quantity,
            product.stock_quantity,
            open_for_decrease=correction_request.open_small_parts_drawer,
        )
        return product
    except HTTPException:
        raise
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
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
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
    service = ProductService(db)
    if not service.delete_product(product_id, performed_by_username=current_user.username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )


@router.post("/{product_id}/image")
@router.post("/{product_id}/image/")
@audited_media("products", "product_id")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Upload product image"""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)
    
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

    AuditLogService(db).log(
        entity_type="product",
        action="IMAGE_UPDATED",
        user_username=current_user.username,
        entity_id=product_id,
        entity_name=product.name,
        new_value={"image_path": image_path},
    )

    db.commit()
    db.refresh(product)
    
    return {"status": "success", "product_id": product_id, "image_path": image_path}


@router.delete("/{product_id}/image")
@router.delete("/{product_id}/image/")
@audited_media("products", "product_id")
async def delete_product_image_file(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete product image and reset stored image path."""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)

    product_repo = ProductRepository(db)
    product = product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    delete_product_image(product_id)
    product.image_path = None
    db.commit()
    db.refresh(product)

    AuditLogService(db).log(entity_type="product", action="IMAGE_DELETED",
        user_username=current_user.username, entity_id=product_id, entity_name=product.name)
    return {"status": "success", "product_id": product_id}


@router.get("/{product_id}/image", dependencies=[Depends(require_session)])
@router.get("/{product_id}/image/", dependencies=[Depends(require_session)])
async def get_product_image(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get product image file"""
    require_authenticated_user(request, db)
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
    
    return FileResponse(file_path, media_type=get_media_type(file_path))



@router.post("/{product_id}/original-image")
@router.post("/{product_id}/original-image/")
@audited_media("products", "product_id")
async def upload_product_original_image(
    product_id: int,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Upload original (uncropped) product image for reset purposes"""
    current_user = require_roles(request, db, UserRole.ADMIN, UserRole.MANAGER)

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
    AuditLogService(db).log(entity_type="product", action="ORIGINAL_IMAGE_UPDATED",
        user_username=current_user.username, entity_id=product_id, entity_name=product.name)
    return {"status": "success", "product_id": product_id}


@router.get("/{product_id}/original-image", dependencies=[Depends(require_session)])
@router.get("/{product_id}/original-image/", dependencies=[Depends(require_session)])
async def get_product_original_image(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get original (uncropped) product image"""
    require_authenticated_user(request, db)
    file_path = get_product_original_image_path(product_id)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original image not found",
        )
    return FileResponse(file_path, media_type=get_media_type(file_path))



@router.post("/{product_id}/categories")
@router.post("/{product_id}/categories/")
@audited_change
async def add_category_to_product(
    product_id: int,
    category_ids: list[int],
    request: Request,
    db: Session = Depends(get_db),
):
    """Add categories to a product (admin only)"""
    current_user = require_roles(request, db, UserRole.ADMIN)
    
    product_repo = ProductRepository(db)
    product = product_repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    
    # Import Category here to avoid circular imports
    from app.models import Category
    
    old_categories = sorted(category.id for category in product.categories)
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
        
        AuditLogService(db).log(entity_type="product", action="CATEGORIES_UPDATED",
            user_username=current_user.username, entity_id=product.id, entity_name=product.name,
            old_value={"category_ids": old_categories},
            new_value={"category_ids": sorted(category.id for category in product.categories)})
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
@audited_change
async def remove_category_from_product(
    product_id: int,
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Remove a category from a product (admin only)"""
    current_user = require_roles(request, db, UserRole.ADMIN)
    
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
        old_categories = sorted(item.id for item in product.categories)
        product.categories.remove(category)
        AuditLogService(db).log(entity_type="product", action="CATEGORIES_UPDATED",
            user_username=current_user.username, entity_id=product.id, entity_name=product.name,
            old_value={"category_ids": old_categories},
            new_value={"category_ids": sorted(item.id for item in product.categories)})
        db.commit()
    
    return {"status": "success"}
