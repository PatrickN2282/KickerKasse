from datetime import date, datetime

from app.services.transaction_export_service import TransactionExportService


def _transaction(**overrides):
    transaction = {
        "id": 12,
        "receipt_number": 1042,
        "created_at": datetime(2026, 9, 4, 19, 35),
        "booking_type": "SALE",
        "type": "SALE",
        "payment_method": "CASH",
        "total_amount_cents": 450,
        "gross_amount_cents": 450,
        "voucher_applied_cents": 0,
        "balance_applied_cents": 0,
        "tip_cents": 75,
        "performed_by": "manager",
        "member": {"id": 7, "name": "Erika Muster"},
        "items": [{
            "id": 21,
            "quantity": 2,
            "unit_price_cents": 225,
            "total_price_cents": 450,
            "note": "Ausgabe <Werkstatt>",
            "product": {"id": 3, "name": "Kreide & Tuch"},
        }],
    }
    transaction.update(overrides)
    return transaction


def test_transaction_export_html_is_printable_and_escapes_content():
    html = TransactionExportService.render_html(
        [_transaction()],
        total_amount_cents=450,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 4),
        payment_method="CASH",
        business_info={"name": "Testverein", "city": "Hannover"},
    )

    assert "TRANSAKTIONSLISTE" in html
    assert "@page" in html
    assert "Testverein" in html
    assert "Kreide &amp; Tuch" in html
    assert "Ausgabe &lt;Werkstatt&gt;" in html
    assert "4,50 €" in html
    assert "0,75 €" in html


def test_transaction_export_csv_uses_semicolon_and_utf8_bom():
    payload = TransactionExportService.render_csv([_transaction()])

    assert payload.startswith(b"\xef\xbb\xbf")
    decoded = payload.decode("utf-8-sig")
    assert "Datum;Zeit;Belegnummer" in decoded
    assert "04.09.2026;19:35;1042;Verkauf;Erika Muster;4,50 €;0,75 €;BAR;manager" in decoded
    assert "2× Kreide & Tuch (Ausgabe <Werkstatt>)" in decoded


def test_dependency_free_pdf_fallback_produces_multiple_valid_pages():
    transactions = [_transaction(id=index, receipt_number=1000 + index) for index in range(90)]

    pdf = TransactionExportService._render_basic_pdf(
        transactions,
        total_amount_cents=40500,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 4),
    )

    assert pdf.startswith(b"%PDF-1.4")
    assert pdf.rstrip().endswith(b"%%EOF")
    assert b"/Count 3" in pdf
    assert b"TRANSAKTIONSLISTE" in pdf
