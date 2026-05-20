import httpx
import pytest
from fastapi import FastAPI

from app.api import import_export as import_export_api


@pytest.fixture
def anyio_backend():
    return "asyncio"


class DummyImportExportService:
    def __init__(self, db):
        self.db = db

    def export_sections(self, sections, include_media):
        return b"zip-content", "application/zip", "import-export.zip"

    def analyze_import(self, file_name, content, media_file_name=None, media_content=None):
        return {
            "data_format": "csv",
            "detected_sections": ["products"],
            "row_counts": {"products": 1},
            "supports_media_sections": ["products"],
            "embedded_media_sections": [],
            "provided_media_sections": [],
            "can_import_media": False,
        }

    def import_sections(
        self,
        file_name,
        content,
        sections=None,
        *,
        import_media=False,
        media_file_name=None,
        media_content=None,
    ):
        return {
            "imported_sections": sections or ["products"],
            "results": {
                "products": {
                    "created": 1,
                    "updated": 0,
                    "media_imported": 0,
                }
            },
        }


def create_app(monkeypatch):
    app = FastAPI()
    app.include_router(import_export_api.router)
    app.dependency_overrides[import_export_api.get_db] = lambda: None

    monkeypatch.setattr(import_export_api, "require_roles", lambda *args, **kwargs: None)
    monkeypatch.setattr(import_export_api, "ImportExportService", DummyImportExportService)

    return app


@pytest.mark.anyio
async def test_export_endpoint_accepts_both_trailing_slash_variants(monkeypatch):
    app = create_app(monkeypatch)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        for path in (
            "/api/admin/import-export/export",
            "/api/admin/import-export/export/",
        ):
            response = await client.post(path, json={"sections": ["products"], "include_media": True})

            assert response.status_code == 200
            assert response.content == b"zip-content"
            assert response.headers["content-disposition"] == 'attachment; filename="import-export.zip"'


@pytest.mark.anyio
async def test_analyze_endpoint_accepts_both_trailing_slash_variants(monkeypatch):
    app = create_app(monkeypatch)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        for path in (
            "/api/admin/import-export/analyze",
            "/api/admin/import-export/analyze/",
        ):
            response = await client.post(
                path,
                files={"data_file": ("products.csv", b"dataset,name\nproducts,Test\n", "text/csv")},
            )

            assert response.status_code == 200
            assert response.json()["detected_sections"] == ["products"]


@pytest.mark.anyio
async def test_import_endpoint_accepts_both_trailing_slash_variants(monkeypatch):
    app = create_app(monkeypatch)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        for path in (
            "/api/admin/import-export/import",
            "/api/admin/import-export/import/",
        ):
            response = await client.post(
                path,
                data={
                    "selected_sections": '["products"]',
                    "import_media": "false",
                },
                files={"data_file": ("products.csv", b"dataset,name\nproducts,Test\n", "text/csv")},
            )

            assert response.status_code == 200
            assert response.json()["imported_sections"] == ["products"]
