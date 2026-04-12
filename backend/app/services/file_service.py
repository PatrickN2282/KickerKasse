"""File handling service for product images and member photos."""
import os
import uuid
from pathlib import Path
from fastapi import UploadFile


UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
PRODUCTS_DIR = UPLOADS_DIR / "products"
MEMBERS_DIR = UPLOADS_DIR / "members"


def ensure_upload_directories():
    """Create upload directories if they don't exist."""
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    MEMBERS_DIR.mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    if "." in filename:
        return "." + filename.rsplit(".", 1)[1].lower()
    return ".jpg"


async def save_product_image(file: UploadFile, product_id: int) -> str:
    """
    Save a product image to disk.
    
    Args:
        file: The uploaded file
        product_id: ID of the product
        
    Returns:
        Relative path to the saved image (e.g., "products/123/image.jpg")
    """
    ensure_upload_directories()
    
    product_folder = PRODUCTS_DIR / str(product_id)
    product_folder.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    ext = get_file_extension(file.filename or "image.jpg")
    filename = f"image{ext}"
    filepath = product_folder / filename
    
    # Save file
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Return relative path
    return f"products/{product_id}/image{ext}"


async def save_member_photo(file: UploadFile, member_id: int) -> str:
    """
    Save a member photo to disk.
    
    Args:
        file: The uploaded file
        member_id: ID of the member
        
    Returns:
        Relative path to the saved photo (e.g., "members/456/photo.jpg")
    """
    ensure_upload_directories()
    
    member_folder = MEMBERS_DIR / str(member_id)
    member_folder.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    ext = get_file_extension(file.filename or "photo.jpg")
    filename = f"photo{ext}"
    filepath = member_folder / filename
    
    # Save file
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Return relative path
    return f"members/{member_id}/photo{ext}"


def delete_product_image(product_id: int) -> None:
    """Delete product image file if it exists."""
    product_folder = PRODUCTS_DIR / str(product_id)
    if product_folder.exists():
        import shutil
        shutil.rmtree(product_folder, ignore_errors=True)


def delete_member_photo(member_id: int) -> None:
    """Delete member photo file if it exists."""
    member_folder = MEMBERS_DIR / str(member_id)
    if member_folder.exists():
        import shutil
        shutil.rmtree(member_folder, ignore_errors=True)


def get_full_path(relative_path: str) -> Path:
    """Get full filesystem path from relative path."""
    if not relative_path:
        return None
    return UPLOADS_DIR / relative_path
