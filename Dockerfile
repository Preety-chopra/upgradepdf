# Backend runtime used by the API, Celery worker, and Celery beat services.
FROM python:3.12-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/tmp/app-home

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-osd \
    ghostscript \
    qpdf \
    pngquant \
    unpaper \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libgl1 \
    libglib2.0-0 \
    fonts-dejavu \
    fonts-liberation \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/storage/uploads /app/storage/outputs /app/storage/ocr_jobs "$HOME" \
    && chown -R appuser:appuser /app "$HOME"

COPY --chown=appuser:appuser backend/ ./

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]


# Frontend development target used by docker-compose.dev.yml.
FROM node:22-alpine AS frontend-development

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./

EXPOSE 5173
CMD ["npm", "run", "dev"]


# Compile the Vue application for production.
FROM frontend-development AS frontend-build

ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build


# Default final target: production frontend served by Nginx.
FROM nginx:1.27-alpine AS frontend-production

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
