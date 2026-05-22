"""File handling service for product images, member photos and branding assets."""
from io import BytesIO
from mimetypes import guess_type
from pathlib import Path

from fastapi import UploadFile
from PIL import Image


UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
PRODUCTS_DIR = UPLOADS_DIR / "products"
MEMBERS_DIR = UPLOADS_DIR / "members"
APP_SETTINGS_DIR = UPLOADS_DIR / "app_settings"


ICON_SPECS = {
    "favicon-16x16.png": 16,
    "favicon-32x32.png": 32,
    "favicon.png": 64,
    "apple-touch-icon.png": 180,
    "icon-192.png": 192,
    "icon-512.png": 512,
}
FAVICON_ICO_SIZES = (16, 32, 48)


def ensure_upload_directories():
    """Create upload directories if they don't exist."""
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    MEMBERS_DIR.mkdir(parents=True, exist_ok=True)
    APP_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_entity_directory(base_dir: Path, entity_id: int) -> Path:
    normalized_id = int(entity_id)
    if normalized_id < 0:
        raise ValueError("Entity ID must be non-negative")

    base_path = base_dir.resolve()
    entity_path = (base_path / str(normalized_id)).resolve()
    _ = entity_path.relative_to(base_path)
    return entity_path


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    if "." in filename:
        return "." + filename.rsplit(".", 1)[1].lower()
    return ".jpg"


async def save_product_image(file: UploadFile, product_id: int) -> str:
    ensure_upload_directories()

    product_folder = _resolve_entity_directory(PRODUCTS_DIR, product_id)
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

    product_folder = _resolve_entity_directory(PRODUCTS_DIR, product_id)
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
    product_folder = _resolve_entity_directory(PRODUCTS_DIR, product_id)
    if not product_folder.exists():
        return None
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        candidate = product_folder / f"original{ext}"
        if candidate.exists():
            return candidate
    return None



async def save_member_photo(file: UploadFile, member_id: int) -> str:
    ensure_upload_directories()

    member_folder = _resolve_entity_directory(MEMBERS_DIR, member_id)
    member_folder.mkdir(parents=True, exist_ok=True)

    ext = get_file_extension(file.filename or "photo.jpg")
    filename = f"photo{ext}"
    filepath = member_folder / filename

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return f"members/{member_id}/photo{ext}"


async def save_member_original_photo(file: UploadFile, member_id: int) -> str:
    ensure_upload_directories()

    member_folder = _resolve_entity_directory(MEMBERS_DIR, member_id)
    member_folder.mkdir(parents=True, exist_ok=True)

    ext = get_file_extension(file.filename or "photo.jpg")
    filename = f"original{ext}"
    filepath = member_folder / filename

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return f"members/{member_id}/original{ext}"


def get_member_original_photo_path(member_id: int) -> Path | None:
    member_folder = _resolve_entity_directory(MEMBERS_DIR, member_id)
    if not member_folder.exists():
        return None
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        candidate = member_folder / f"original{ext}"
        if candidate.exists():
            return candidate
    return None


async def save_app_logo(file: UploadFile) -> str:
    ensure_upload_directories()

    content = await file.read()
    image = Image.open(BytesIO(content)).convert("RGBA")

    logo_path = APP_SETTINGS_DIR / "logo.png"
    image.save(logo_path, format="PNG")

    def create_square_icon(size: int) -> Image.Image:
        icon_canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        resized = image.copy()
        resized.thumbnail((size, size), Image.Resampling.LANCZOS)
        x_offset = (size - resized.width) // 2
        y_offset = (size - resized.height) // 2
        icon_canvas.paste(resized, (x_offset, y_offset), resized)
        return icon_canvas

    for filename, size in ICON_SPECS.items():
        create_square_icon(size).save(APP_SETTINGS_DIR / filename, format="PNG")

    favicon_sources = [create_square_icon(size) for size in FAVICON_ICO_SIZES]
    favicon_sources[0].save(
        APP_SETTINGS_DIR / "favicon.ico",
        format="ICO",
        sizes=[(size, size) for size in FAVICON_ICO_SIZES],
        append_images=favicon_sources[1:],
    )

    return "app_settings/logo.png"


async def save_kasse_products_background(file: UploadFile) -> str:
    ensure_upload_directories()

    content = await file.read()
    image = Image.open(BytesIO(content)).convert("RGBA")

    background_path = APP_SETTINGS_DIR / "kasse_products_background.png"
    image.save(background_path, format="PNG")

    return "app_settings/kasse_products_background.png"


def delete_product_image(product_id: int) -> None:
    product_folder = _resolve_entity_directory(PRODUCTS_DIR, product_id)
    if product_folder.exists():
        import shutil
        shutil.rmtree(product_folder, ignore_errors=True)


def delete_member_photo(member_id: int) -> None:
    member_folder = _resolve_entity_directory(MEMBERS_DIR, member_id)
    if member_folder.exists():
        import shutil
        shutil.rmtree(member_folder, ignore_errors=True)


def get_full_path(relative_path: str) -> Path | None:
    if not relative_path:
        return None
    return UPLOADS_DIR / relative_path


def get_media_type(file_path: Path) -> str:
    """Return the detected MIME type for a stored file path."""
    media_type, _ = guess_type(file_path.name)
    return media_type or "application/octet-stream"
