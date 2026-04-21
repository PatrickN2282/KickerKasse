from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core import get_db
from app.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from app.repositories import CategoryRepository, UserRepository
from app.models import UserRole

router = APIRouter(prefix="/api/categories", tags=["Categories"])


def _require_admin(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    current_user = UserRepository(db).get_by_id(user_id)
    if not current_user or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return current_user


@router.get("/", response_model=list[CategoryResponse])
@router.get("", response_model=list[CategoryResponse])
async def get_categories(
    request: Request,
    only_active: bool = False,
    db: Session = Depends(get_db),
):
    """Get all categories"""
    if not request.session.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    repo = CategoryRepository(db)
    return repo.get_all(only_active=only_active)


@router.get("/{category_id}", response_model=CategoryResponse)
@router.get("/{category_id}/", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get category by ID"""
    if not request.session.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    repo = CategoryRepository(db)
    category = repo.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    return category


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Create a new category (admin only)"""
    _require_admin(request, db)
    
    try:
        repo = CategoryRepository(db)
        category = repo.create(
            name=category_data.name,
            description=category_data.description,
            is_active_in_kasse=category_data.is_active_in_kasse,
            display_order=category_data.display_order,
        )
        return category
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists",
        )


@router.put("/{category_id}", response_model=CategoryResponse)
@router.put("/{category_id}/", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update category (admin only)"""
    _require_admin(request, db)
    
    try:
        repo = CategoryRepository(db)
        category = repo.update(
            category_id,
            name=category_data.name,
            description=category_data.description,
            is_active_in_kasse=category_data.is_active_in_kasse,
            display_order=category_data.display_order,
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        return category
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists",
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{category_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete category (admin only)"""
    _require_admin(request, db)
    
    repo = CategoryRepository(db)
    if not repo.delete(category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )


@router.post("/{category_id}/products")
@router.post("/{category_id}/products/")
async def assign_products_to_category(
    category_id: int,
    product_ids: list[int],
    request: Request,
    db: Session = Depends(get_db),
):
    """Assign multiple products to a category (admin only)."""
    _require_admin(request, db)

    from app.models import Category, Product

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    assigned = 0
    for product_id in set(product_ids):
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            continue
        if category not in product.categories:
            product.categories.append(category)
            assigned += 1

    db.commit()
    return {"status": "success", "assigned": assigned, "category_id": category_id}


@router.delete("/{category_id}/products/{product_id}")
@router.delete("/{category_id}/products/{product_id}/")
async def remove_product_from_category(
    category_id: int,
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Remove one product from a category (admin only)."""
    _require_admin(request, db)

    from app.models import Category, Product

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if category in product.categories:
        product.categories.remove(category)
        db.commit()

    return {"status": "success", "category_id": category_id, "product_id": product_id}
