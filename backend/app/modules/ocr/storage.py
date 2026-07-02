from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, UploadFile

OCR_STORAGE_DIR = Path(os.getenv("OCR_STORAGE_DIR", "/app/storage/ocr_jobs"))
MAX_UPLOAD_MB = int(os.getenv("OCR_MAX_UPLOAD_MB", "100"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
ALLOWED_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_filename(filename: str | None, fallback: str = "upload") -> str:
    name = Path(filename or fallback).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return name or fallback


def create_job_id() -> str:
    return uuid4().hex


def get_job_dir(job_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{32}", job_id):
        raise HTTPException(status_code=400, detail="Invalid OCR job id.")
    return OCR_STORAGE_DIR / job_id


def status_path(job_id: str) -> Path:
    return get_job_dir(job_id) / "status.json"


def read_status(job_id: str) -> dict[str, Any]:
    path = status_path(job_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="OCR job not found.")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="OCR job status is corrupted.") from exc


def write_status(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    job_dir = get_job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = utc_now()
    path = status_path(job_id)
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)
    return data


def update_status(job_id: str, **changes: Any) -> dict[str, Any]:
    data = read_status(job_id)
    data.update(changes)
    return write_status(job_id, data)


async def save_ocr_upload(file: UploadFile, job_dir: Path) -> Path:
    original_name = safe_filename(file.filename, fallback="upload.pdf")
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed}")

    input_dir = job_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    upload_path = input_dir / original_name

    total = 0
    try:
        with upload_path.open("wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail=f"File too large. Limit is {MAX_UPLOAD_MB} MB.")
                output.write(chunk)
    finally:
        await file.close()

    if total == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return upload_path


def public_status_payload(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": data.get("job_id"),
        "status": data.get("status", "queued"),
        "percent": int(data.get("percent", 0)),
        "message": data.get("message", ""),
        "filename": data.get("filename"),
        "language": data.get("language"),
        "page_count": data.get("page_count"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "completed_at": data.get("completed_at"),
        "output_pdf_available": bool(data.get("output_pdf")),
        "output_text_available": bool(data.get("output_text")),
        "error": data.get("error"),
    }
