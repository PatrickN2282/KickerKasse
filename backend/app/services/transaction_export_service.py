"""Export helpers for the filtered transaction history."""

from __future__ import annotations

import csv
from datetime import date, datetime
from html import escape
from io import BytesIO, StringIO
from textwrap import shorten

from app.services.zbon_html_exporter import ZBonHTMLExporter


class TransactionExportService:
    """Render one transaction selection consistently as HTML, CSV and PDF."""

    BOOKING_TYPE_LABELS = {
        "SALE": "Verkauf",
        "STORNO": "Storno",
        "RECHARGE": "Aufladung",
        "MEMBER_BALANCE_RECHARGE": "Mitgliedsguthaben",
        "CLUB_ACCOUNT_TOP_UP": "Gutscheinkonto",
        "GIFT_VOUCHER_CREATE": "Gutschein erstellt",
        "PREPAID_VOUCHER_CREATE": "Verzehrkarte erstellt",
        "VOUCHER_REDEMPTION": "Einlösung",
        "VOUCHER_SALE": "Gutscheinverkauf",
        "CASH_WITHDRAWAL": "Abschöpfung",
        "CASH_DEPOSIT": "Einlage",
    }
    PAYMENT_LABELS = {
        "CASH": "BAR",
        "BALANCE": "Guthaben",
        "VOUCHER_GIFT": "Gutschein",
        "VOUCHER_PREPAID": "Verzehrkarte",
        "WITHDRAWAL": "Abschöpfung",
    }

    @classmethod
    def transaction_type_label(cls, transaction: dict) -> str:
        booking_type = transaction.get("booking_type") or transaction.get("type") or ""
        return cls.BOOKING_TYPE_LABELS.get(booking_type, booking_type or "-")

    @classmethod
    def payment_label(cls, transaction: dict) -> str:
        parts: list[str] = []
        voucher_type = transaction.get("voucher_type")
        if transaction.get("voucher_applied_cents"):
            parts.append("Gutschein" if voucher_type == "GIFT" else "Verzehrkarte")
        payment_method = transaction.get("payment_method") or ""
        if payment_method == "BALANCE" or transaction.get("balance_applied_cents"):
            parts.append("Guthaben")
        if payment_method == "CASH" and transaction.get("total_amount_cents"):
            parts.append("BAR")
        if not parts:
            parts.append(cls.PAYMENT_LABELS.get(payment_method, payment_method or "-"))
        return " + ".join(dict.fromkeys(parts))

    @staticmethod
    def member_label(transaction: dict) -> str:
        booking_type = transaction.get("booking_type")
        if booking_type == "CASH_WITHDRAWAL":
            return "Abschöpfung"
        if booking_type == "CLUB_ACCOUNT_TOP_UP":
            return "Gutscheinkonto"
        if booking_type in {"GIFT_VOUCHER_CREATE", "PREPAID_VOUCHER_CREATE"}:
            return "Gutscheinsystem"
        return (transaction.get("member") or {}).get("name") or transaction.get("member_name") or "Gast"

    @staticmethod
    def user_label(transaction: dict) -> str:
        return transaction.get("performed_by") or (transaction.get("user") or {}).get("username") or "-"

    @staticmethod
    def item_label(transaction: dict) -> str:
        items = []
        for item in transaction.get("items") or []:
            product_name = (item.get("product") or {}).get("name") or f"Artikel {item.get('id', '-')}"
            text = f"{item.get('quantity', 0)}× {product_name}"
            if item.get("note"):
                text += f" ({item['note']})"
            items.append(text)
        return "; ".join(items) or transaction.get("reason") or "-"

    @staticmethod
    def _format_datetime(value) -> tuple[str, str]:
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return value, ""
        if not isinstance(value, datetime):
            return "-", "-"
        return value.strftime("%d.%m.%Y"), value.strftime("%H:%M")

    @staticmethod
    def _format_euro(cents) -> str:
        amount = int(cents or 0) / 100
        return f"{amount:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

    @classmethod
    def _rows(cls, transactions: list[dict]) -> list[dict]:
        rows = []
        for transaction in transactions:
            date_text, time_text = cls._format_datetime(transaction.get("created_at"))
            rows.append({
                "date": date_text,
                "time": time_text,
                "receipt": transaction.get("receipt_number") or "-",
                "type": cls.transaction_type_label(transaction),
                "member": cls.member_label(transaction),
                "amount": cls._format_euro(transaction.get("gross_amount_cents", transaction.get("total_amount_cents"))),
                "tip": cls._format_euro(transaction.get("tip_cents")) if transaction.get("tip_cents") else "-",
                "payment": cls.payment_label(transaction),
                "user": cls.user_label(transaction),
                "items": cls.item_label(transaction),
            })
        return rows

    @staticmethod
    def filename(start_date: date, end_date: date, suffix: str) -> str:
        return f"Transaktionen_{start_date.isoformat()}_{end_date.isoformat()}.{suffix}"

    @classmethod
    def render_html(
        cls,
        transactions: list[dict],
        total_amount_cents: int,
        start_date: date,
        end_date: date,
        payment_method: str | None,
        business_info: dict | None = None,
    ) -> str:
        business_info = business_info or {}
        rows = cls._rows(transactions)
        payment_filter = cls.PAYMENT_LABELS.get(payment_method or "", "Alle Zahlungsarten")
        business_location = " ".join(
            part for part in [business_info.get("street"), business_info.get("zip"), business_info.get("city")] if part
        )
        body_rows = "".join(
            f"""
            <tr>
              <td>{escape(row['date'])}<br><small>{escape(row['time'])}</small></td>
              <td class="num">{escape(str(row['receipt']))}</td>
              <td>{escape(row['type'])}</td>
              <td>{escape(row['member'])}</td>
              <td class="amount">{escape(row['amount'])}</td>
              <td class="amount">{escape(row['tip'])}</td>
              <td>{escape(row['payment'])}</td>
              <td>{escape(row['user'])}</td>
              <td class="items">{escape(row['items'])}</td>
            </tr>"""
            for row in rows
        ) or '<tr><td colspan="9" class="empty">Keine Transaktionen im gewählten Zeitraum</td></tr>'

        return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Transaktionsliste</title>
  <style>
    @page {{ size: A4 landscape; margin: 12mm; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: #172033; font: 12px Arial, sans-serif; background: #eef2f6; }}
    .report {{ width: min(1200px, calc(100% - 32px)); margin: 18px auto; background: #fff; padding: 28px; box-shadow: 0 8px 30px rgba(15,23,42,.12); }}
    header {{ border-bottom: 4px solid #0f766e; padding-bottom: 14px; margin-bottom: 18px; display: flex; justify-content: space-between; gap: 24px; }}
    h1 {{ margin: 0 0 5px; font-size: 24px; letter-spacing: .04em; }}
    .business {{ font-weight: 700; color: #0f766e; }}
    .meta {{ text-align: right; line-height: 1.6; }}
    .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 0 0 18px; }}
    .summary div {{ border: 1px solid #d9e1e8; border-radius: 8px; padding: 10px 12px; background: #f8fafc; }}
    .summary span {{ display: block; color: #64748b; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; }}
    .summary strong {{ display: block; margin-top: 4px; font-size: 16px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
    thead {{ display: table-header-group; }}
    th {{ padding: 8px 6px; color: #fff; background: #1f2937; text-align: left; text-transform: uppercase; letter-spacing: .03em; }}
    td {{ padding: 7px 6px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
    tbody tr:nth-child(even) {{ background: #f8fafc; }}
    .amount {{ text-align: right; white-space: nowrap; font-weight: 700; }}
    .num {{ text-align: center; }}
    .items {{ max-width: 310px; color: #475569; }}
    .empty {{ text-align: center; padding: 28px; color: #64748b; }}
    footer {{ margin-top: 18px; padding-top: 10px; border-top: 1px solid #d9e1e8; color: #64748b; font-size: 9px; }}
    @media print {{ body {{ background: #fff; }} .report {{ width: 100%; margin: 0; padding: 0; box-shadow: none; }} }}
  </style>
</head>
<body>
  <main class="report">
    <header>
      <div><div class="business">{escape(business_info.get('name') or 'KickerKasse')}</div><h1>TRANSAKTIONSLISTE</h1><div>{escape(business_location)}</div></div>
      <div class="meta"><strong>Zeitraum</strong><br>{start_date.strftime('%d.%m.%Y')} bis {end_date.strftime('%d.%m.%Y')}<br>{escape(payment_filter)}</div>
    </header>
    <section class="summary">
      <div><span>Transaktionen</span><strong>{len(rows)}</strong></div>
      <div><span>Summe</span><strong>{escape(cls._format_euro(total_amount_cents))}</strong></div>
      <div><span>Erstellt am</span><strong>{datetime.now().strftime('%d.%m.%Y %H:%M')}</strong></div>
    </section>
    <table>
      <thead><tr><th>Datum / Zeit</th><th>Beleg</th><th>Typ</th><th>Mitglied / Konto</th><th class="amount">Betrag</th><th class="amount">Trinkgeld</th><th>Zahlungsart</th><th>Benutzer</th><th>Positionen / Grund</th></tr></thead>
      <tbody>{body_rows}</tbody>
    </table>
    <footer>Erzeugt mit KickerKasse · Auswahl entspricht den Filtern der Transaktionshistorie.</footer>
  </main>
</body>
</html>"""

    @classmethod
    def render_csv(cls, transactions: list[dict]) -> bytes:
        output = StringIO(newline="")
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Datum", "Zeit", "Belegnummer", "Typ", "Mitglied / Konto", "Betrag", "Trinkgeld", "Zahlungsart", "Benutzer", "Positionen / Grund"])
        for row in cls._rows(transactions):
            writer.writerow([row["date"], row["time"], row["receipt"], row["type"], row["member"], row["amount"], row["tip"], row["payment"], row["user"], row["items"]])
        return ("\ufeff" + output.getvalue()).encode("utf-8")

    @classmethod
    def render_pdf(cls, html_content: str, transactions: list[dict], total_amount_cents: int, start_date: date, end_date: date) -> bytes:
        """Use the HTML renderer when available and a dependency-free PDF fallback otherwise."""
        try:
            return ZBonHTMLExporter.export_pdf(html_content).getvalue()
        except RuntimeError:
            return cls._render_basic_pdf(transactions, total_amount_cents, start_date, end_date)

    @classmethod
    def _render_basic_pdf(cls, transactions: list[dict], total_amount_cents: int, start_date: date, end_date: date) -> bytes:
        header = f"TRANSAKTIONSLISTE  {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        lines = [
            header,
            f"Anzahl: {len(transactions)}    Summe: {cls._format_euro(total_amount_cents)}",
            "Datum Zeit | Beleg | Typ | Mitglied/Konto | Betrag | Trinkgeld | Zahlung | Benutzer | Positionen/Grund",
        ]
        for row in cls._rows(transactions):
            lines.append(shorten(
                f"{row['date']} {row['time']} | {row['receipt']} | {row['type']} | {row['member']} | {row['amount']} | {row['tip']} | {row['payment']} | {row['user']} | {row['items']}",
                width=156,
                placeholder="...",
            ))
        if not transactions:
            lines.append("Keine Transaktionen im gewählten Zeitraum")

        page_size = 43
        pages = [lines[index:index + page_size] for index in range(0, len(lines), page_size)]
        return cls._build_pdf_document(pages)

    @staticmethod
    def _pdf_text(value: str) -> bytes:
        encoded = value.encode("cp1252", errors="replace")
        return encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")

    @classmethod
    def _build_pdf_document(cls, pages: list[list[str]]) -> bytes:
        page_count = len(pages)
        font_id = 3 + page_count * 2
        objects: dict[int, bytes] = {
            1: b"<< /Type /Catalog /Pages 2 0 R >>",
            font_id: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        }
        page_ids = []
        for index, page_lines in enumerate(pages):
            page_id = 3 + index * 2
            content_id = page_id + 1
            page_ids.append(page_id)
            stream_parts = [b"BT", b"/F1 13 Tf", b"40 560 Td"]
            for line_index, line in enumerate(page_lines):
                if line_index == 1:
                    stream_parts.extend([b"/F1 9 Tf", b"0 -24 Td"])
                elif line_index > 1:
                    stream_parts.append(b"0 -12 Td")
                stream_parts.append(b"(" + cls._pdf_text(line) + b") Tj")
            stream_parts.extend([b"ET", b"0.75 w", b"40 522 m 802 522 l S"])
            stream = b"\n".join(stream_parts)
            objects[page_id] = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode("ascii")
            objects[content_id] = f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream"
        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode("ascii")

        buffer = BytesIO()
        buffer.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0] * (font_id + 1)
        for object_id in range(1, font_id + 1):
            offsets[object_id] = buffer.tell()
            buffer.write(f"{object_id} 0 obj\n".encode("ascii"))
            buffer.write(objects[object_id])
            buffer.write(b"\nendobj\n")
        xref_offset = buffer.tell()
        buffer.write(f"xref\n0 {font_id + 1}\n".encode("ascii"))
        buffer.write(b"0000000000 65535 f \n")
        for object_id in range(1, font_id + 1):
            buffer.write(f"{offsets[object_id]:010d} 00000 n \n".encode("ascii"))
        buffer.write(f"trailer\n<< /Size {font_id + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode("ascii"))
        return buffer.getvalue()
