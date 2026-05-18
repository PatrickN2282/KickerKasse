# PDF Export Feature - Optional Configuration

## Status

The PDF export feature for Z-Bon reports is now **optional**. The system works perfectly fine without it:
- ✅ Z-Bon HTML reports work
- ✅ Browser printing (Ctrl+P) works for all reports
- ⚠️ PDF download endpoint falls back to HTML view if WeasyPrint not available

## Why Optional?

WeasyPrint requires complex system libraries (cairo, pango, pixbuf, etc.) that:
- Add ~500MB to Docker image size
- Can cause build failures in some environments (like Portainer)
- Aren't necessary if you're printing from the browser instead

## Default Setup (Quick Deployment) ✅

The standard `docker-compose.yml` and `requirements.txt` don't include WeasyPrint.

**Deploy with:**
```bash
docker-compose build --no-cache
docker-compose up
```

**Features available:**
- View Z-Bon as HTML in browser
- Print Z-Bon using browser print (Ctrl+P, then "Save as PDF")
- All other system functionality

## Optional: Enable PDF Export

If you need server-side PDF generation for email attachments or archival:

### Option 1: Using requirements-full.txt (Easy)

```bash
# Development/testing only
pip install -r backend/requirements-full.txt
```

### Option 2: Docker with PDF Support

Create a custom Dockerfile:

```dockerfile
# Copy the standard Dockerfile
# Then add these lines after the pip upgrade but before installing requirements.txt:

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libcairo2-dev \
    libpango-1.0-0 \
    libpango-1.0-dev \
    libgdk-pixbuf-2.0-0 \
    libgdk-pixbuf-2.0-dev \
    libpng-dev \
    libjpeg62-turbo-dev \
    libfreetype6-dev \
    zlib1g-dev \
    libfontconfig1-dev \
    && rm -rf /var/lib/apt/lists/*

# Then copy this Dockerfile to backend/ and update docker-compose.yml:
# dockerfile: backend/Dockerfile.full
```

Then uncomment `weasyprint==59.3` in `backend/requirements.txt`:

```bash
# backend/requirements.txt
# ... other packages ...

# Optional: PDF export support (uncomment to enable)
weasyprint==59.3
```

Build and deploy:
```bash
docker-compose build --no-cache
docker-compose up
```

## API Endpoints

### Get Z-Bon as HTML
```
GET /api/transactions/zbon/html?report_date=2026-04-14
```
Returns: HTML page for browser viewing/printing

### Get Z-Bon as PDF (Optional)
```
GET /api/transactions/zbon/pdf?report_date=2026-04-14
```

**Behavior:**
- If WeasyPrint is installed: Returns PDF file download
- If WeasyPrint is not installed: Returns HTML with fallback message + print instructions

## Troubleshooting

### WeasyPrint installation fails locally
This typically happens due to missing system libraries. Instead of fixing locally, just:
1. Use the HTML endpoint for viewing/printing
2. Or use a full Docker build with the provided libraries

### Want to check if PDF export is available?
Check the logs:
```bash
# If you see this warning on startup, PDF export is disabled:
# WARNING - WeasyPrint not available - PDF export disabled
```

### Need to debug the current state?
```bash
# In the running container:
docker exec <container-name> python -c "import weasyprint; print('WeasyPrint available')"
# Or:
docker exec <container-name> python -c "from app.services.zbon_html_exporter import WEASYPRINT_AVAILABLE; print('PDF support:', WEASYPRINT_AVAILABLE)"
```

## Summary

- **Default**: Lightweight, always works, HTML + browser print
- **Optional**: Add WeasyPrint for server-side PDF generation
- **Fallback**: PDF endpoint gracefully degrades to HTML view with instructions

Choose based on your deployment environment and needs.
