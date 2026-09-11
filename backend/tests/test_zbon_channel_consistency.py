from datetime import date

from app.services.zbon_service import ZBonService


def _canonical_payload():
    return {
        "sequence_number": 7,
        "business_date": "2026-08-31",
        "period_start": "2026-08-30T10:00:00",
        "period_end": "2026-08-31T18:00:00",
        "summary": {"cash_calculated_cents": 12345},
        "report_content": "<html>canonical</html>",
    }


def test_daily_email_update_uses_canonical_preview(monkeypatch):
    service = object.__new__(ZBonService)
    monkeypatch.setattr(service, "build_current_zbon_preview", lambda: _canonical_payload())

    result = service.generate_daily_html_update(date(2026, 8, 30))

    assert result["html"] == result["report_content"]
    assert result["business_date"] == "2026-08-31"
    assert result["requested_date"] == "2026-08-30"
    assert result["summary"]["cash_calculated_cents"] == 12345


def test_legacy_generate_endpoint_uses_canonical_preview(monkeypatch):
    service = object.__new__(ZBonService)
    captured = {}

    def preview(**kwargs):
        captured.update(kwargs)
        return _canonical_payload()

    monkeypatch.setattr(service, "build_current_zbon_preview", preview)

    result = service.generate_zbon(
        target_date=date(2026, 8, 30),
        include_cash_count={"coins": {"1": 2}, "notes": {}},
        report_type="full-zbon",
    )

    assert result["content"] == result["report_content"]
    assert result["stats"] is result["summary"]
    assert result["date"] == result["business_date"]
    assert captured["include_cash_count"]["coins"]["1"] == 2
