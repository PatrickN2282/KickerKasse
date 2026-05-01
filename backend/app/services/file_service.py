"""File handling service for product images, member photos and branding assets."""
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from PIL import Image


UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
PRODUCTS_DIR = UPLOADS_DIR / "products"
MEMBERS_DIR = UPLOADS_DIR / "members"
APP_SETTINGS_DIR = UPLOADS_DIR / "app_settings"


ICON_SPECS = {
    "favicon.png": 64,
    "apple-touch-icon.png": 180,
    "icon-192.png": 192,
    "icon-512.png": 512,
}


def ensure_upload_directories():
    """Create upload directories if they don't exist."""
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    MEMBERS_DIR.mkdir(parents=True, exist_ok=True)
    APP_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    if "." in filename:
        return "." + filename.rsplit(".", 1)[1].lower()
    return ".jpg"


async def save_product_image(file: UploadFile, product_id: int) -> str:
    ensure_upload_directories()

    product_folder = PRODUCTS_DIR / str(product_id)
    product_folder.mkdir(parents=True, exist_ok=True)

    ext = get_file_extension(file.filename or "image.jpg")
    filename = f"image{ext}"
    filepath = product_folder / filename

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return f"products/{product_id}/image{ext}"


async def save_product_original_image(file: UploadFile, product_id: int) -> str:
    ensure_upload_directories()

    product_folder = PRODUCTS_DIR / str(product_id)
    product_folder.mkdir(parents=True, exist_ok=True)

    ext = get_file_extension(file.filename or "image.jpg")
    filename = f"original{ext}"
    filepath = product_folder / filename

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return f"products/{product_id}/original{ext}"


def get_product_original_image_path(product_id: int) -> Path | None:
    """Return path to original image if it exists (any extension)."""
    product_folder = PRODUCTS_DIR / str(product_id)
    if not product_folder.exists():
        return None
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        candidate = product_folder / f"original{ext}"
        if candidate.exists():
            return candidate
    return None



async def save_member_photo(file: UploadFile, member_id: int) -> str:
    ensure_upload_directories()

    member_folder = MEMBERS_DIR / str(member_id)
    member_folder.mkdir(parents=True, exist_ok=True)

    ext = get_file_extension(file.filename or "photo.jpg")
    filename = f"photo{ext}"
    filepath = member_folder / filename

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return f"members/{member_id}/photo{ext}"


async def save_app_logo(file: UploadFile) -> str:
    ensure_upload_directories()

    content = await file.read()
    image = Image.open(BytesIO(content)).convert("RGBA")

    logo_path = APP_SETTINGS_DIR / "logo.png"
    image.save(logo_path, format="PNG")

    for filename, size in ICON_SPECS.items():
        icon_canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        resized = image.copy()
        resized.thumbnail((size, size), Image.Resampling.LANCZOS)
        x_offset = (size - resized.width) // 2
        y_offset = (size - resized.height) // 2
        icon_canvas.paste(resized, (x_offset, y_offset), resized)
        icon_canvas.save(APP_SETTINGS_DIR / filename, format="PNG")

    return "app_settings/logo.png"


def delete_product_image(product_id: int) -> None:
    product_folder = PRODUCTS_DIR / str(product_id)
    if product_folder.exists():
        import shutil
        shutil.rmtree(product_folder, ignore_errors=True)


def delete_member_photo(member_id: int) -> None:
    member_folder = MEMBERS_DIR / str(member_id)
    if member_folder.exists():
        import shutil
        shutil.rmtree(member_folder, ignore_errors=True)


def get_full_path(relative_path: str) -> Path | None:
    if not relative_path:
        return None
    return UPLOADS_DIR / relative_path
