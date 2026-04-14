# Z-Bon HTML Rendering & Email Integration

## Overview

The KickerKasse system now provides professional HTML-based Z-Bon rendering for both web display and email distribution, replacing the old text-based format.

## Features

### 1. Browser Display & Download
- **Endpoint**: `GET /api/transactions/zbon/html`
- **Format**: Professional HTML with CSS styling
- **Use Case**: View in browser, print to PDF using browser print dialog
- **Query Parameters**:
  - `report_date`: Optional (YYYY-MM-DD format, defaults to today)

**Example**:
```bash
curl -H "Cookie: session=$SESSION_ID" \
  http://localhost:8000/api/transactions/zbon/html?report_date=2026-04-14
```

### 2. Professional Email Distribution
- **Endpoint**: `POST /api/transactions/zbon/email`
- **Format**: Email-optimized HTML (table-based layout for maximum compatibility)
- **Query/Body Parameters**:
  - `recipient`: Email address (required)
  - `report_date`: Optional (YYYY-MM-DD format, defaults to today)
  - `include_pdf`: Optional boolean (attach PDF if WeasyPrint available)

**Example**:
```bash
curl -X POST -H "Cookie: session=$SESSION_ID" \
  "http://localhost:8000/api/transactions/zbon/email?recipient=manager@example.com&report_date=2026-04-14&include_pdf=true"
```

**Response**:
```json
{
  "status": "success",
  "message": "Z-Bon sent to manager@example.com",
  "date": "2026-04-14",
  "seq_number": 42,
  "pdf_attached": true
}
```

### 3. Optional PDF Download
- **Endpoint**: `GET /api/transactions/zbon/pdf`
- **Format**: PDF file (if WeasyPrint available, otherwise HTML fallback)
- **Query Parameters**:
  - `report_date`: Optional (YYYY-MM-DD format, defaults to today)

**Example**:
```bash
curl -H "Cookie: session=$SESSION_ID" \
  http://localhost:8000/api/transactions/zbon/pdf?report_date=2026-04-14 \
  -o Z-Bon_2026-04-14.pdf
```

## Templates

### Standard Display Template (`zbon_template.py`)
- **Purpose**: Browser viewing with full features
- **Layout**: Modern CSS-based design
- **Features**:
  - Blue highlighted sections
  - Yellow summary box
  - Full cash count breakdown
  - Category/customer/tax rate aggregations
  - Storno details
  - Color-coded highlights
  - Print-optimized styles

### Email Template (`zbon_email_template.py`)
- **Purpose**: Maximum compatibility with email clients
- **Layout**: Table-based (Gmail, Outlook, Apple Mail compatible)
- **Features**:
  - Inline styles (no external CSS)
  - Fixed 600px width for mobile compatibility
  - Fallback fonts
  - Simplified layout focusing on key info
  - Works in all email clients

## Usage Examples

### Manual Z-Bon Download (HTML)
```python
# User manually generates and views Z-Bon in browser
GET /api/transactions/zbon/html

# User prints to PDF via browser (Ctrl+P → Save as PDF)
```

### Send Z-Bon to Manager Daily
```python
# Backend scheduler sends daily Z-Bon
POST /api/transactions/zbon/email
{
  "recipient": "manager@kickerkasse.local",
  "report_date": "2026-04-14",
  "include_pdf": true
}
```

### Monthly Archive with PDF
```python
# Archive department receives monthly Z-Böns as PDF
for day in range(1, 31):
    date = f"2026-04-{day:02d}"
    POST /api/transactions/zbon/email
    {
      "recipient": "archive@example.com",
      "report_date": date,
      "include_pdf": true
    }
```

## Email Service Integration

The `EmailService` now includes:

### `send_zbon_email(recipient, zbon_content, date)`
- **Legacy method** for text-based Z-Bon
- Uses plain text + HTML fallback
- TXT file attachment

### `send_zbon_html_email(recipient, html_zbon, date, seq_number, include_pdf)`
- **New method** for HTML-based Z-Bon
- Email-optimized HTML template
- Optional PDF attachment
- Professional formatting

**Implementation**:
```python
from app.services import EmailService
from app.services.zbon_html_exporter import ZBonHTMLExporter

# Render email-friendly HTML
email_html = ZBonHTMLExporter.render_email_html(
    seq_number=42,
    business_date="2026-04-14",
    # ... other parameters
)

# Send via email
EmailService.send_zbon_html_email(
    recipient="manager@example.com",
    html_zbon=email_html,
    date="2026-04-14",
    seq_number=42,
    include_pdf=pdf_bytes  # Optional
)
```

## Rendering Options

### Browser Display (Full Template)
```python
html = ZBonHTMLExporter.render_html(
    seq_number=42,
    business_date="2026-04-14",
    # ... all parameters
)
# Returns: Full-featured HTML for browser display
```

### Email Display (Email Template)
```python
html = ZBonHTMLExporter.render_email_html(
    seq_number=42,
    business_date="2026-04-14",
    # ... key parameters only
)
# Returns: Email-safe table-based HTML
```

### PDF Export (Optional)
```python
html = ZBonHTMLExporter.render_html(...)
pdf_bytes = ZBonHTMLExporter.export_pdf(html)
# Returns: BytesIO object with PDF content
```

## Configuration

### Email Settings (backend/.env)
```bash
EMAIL_ENABLED=true
EMAIL_SENDER=noreply@kickerkasse.local
SMTP_HOST=mail.example.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=smtp_user
SMTP_PASSWORD=smtp_password
```

### Optional PDF Support
If you want PDF attachments in emails:
```bash
# Install full requirements with WeasyPrint
pip install -r backend/requirements-full.txt

# Or enable in Docker (see PDF_EXPORT_OPTIONAL.md)
```

## Frontend Integration

### Button: "Email Z-Bon"
```javascript
async function sendZBonEmail(email, date) {
  const response = await fetch('/api/transactions/zbon/email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      recipient: email,
      report_date: date,
      include_pdf: true
    })
  });
  return await response.json();
}
```

### Button: "Download HTML"
```javascript
function downloadZBonHTML(date) {
  window.location.href = `/api/transactions/zbon/html?report_date=${date}`;
}
```

### Button: "Download PDF"
```javascript
function downloadZBonPDF(date) {
  window.location.href = `/api/transactions/zbon/pdf?report_date=${date}`;
}
```

## Troubleshooting

### Z-Bon doesn't render in email?
- Check email client compatibility (use inline styles)
- Verify `zbon_email_template.py` is using table-based layout
- Test with `zbon_template.py` in browser first

### PDF attachment missing?
- WeasyPrint may not be installed (check logs)
- Use fallback HTML view instead
- See `PDF_EXPORT_OPTIONAL.md` for installation

### Email not sent?
- Verify `EMAIL_ENABLED=true` in `.env`
- Check SMTP settings
- View server logs for error details

## Performance Notes

- HTML rendering: ~50-100ms per Z-Bon
- PDF generation: ~500-1000ms per Z-Bon (if enabled)
- Email sending: ~2-5s per recipient (network dependent)
- Consider async task queue for bulk sendings

## Future Enhancements

- [ ] Scheduled Z-Bon email delivery
- [ ] Z-Bon archival with search/retrieval
- [ ] Multi-recipient bulk email
- [ ] Electronic signature for compliance
- [ ] QR code for verification
- [ ] Multi-format support (Excel, CSV)
