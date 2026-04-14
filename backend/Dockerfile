# Multi-Stage Dockerfile für Kassensoftware
# Stage 1: Build Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
# Force-install dev dependencies for build tools like vite, even if NODE_ENV=production is set by CI/Portainer.
RUN npm ci --include=dev
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend mit integriertem Frontend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app app/
COPY backend/main.py .

# Create frontend directory for copying dist
RUN mkdir -p /app/app/frontend

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist /app/app/frontend/dist

# Create upload directories
RUN mkdir -p /app/uploads/products /app/uploads/members

# Copy entrypoint script
COPY backend/docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 8000), timeout=5)"

# Expose port
EXPOSE 8000

# Start the application with entrypoint script for automatic migrations
ENTRYPOINT ["/app/docker-entrypoint.sh"]
