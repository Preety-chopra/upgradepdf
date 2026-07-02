import os
import uuid
from pathlib import Path
from typing import List

from fastapi import UploadFile, HTTPException

from app.core.config import settings


ALLOWED_MIME_TYPES = {
    "application/pdf",
}


def create_job_id() -> str:
    return str(uuid.uuid4())


def get_upload_path(job_id: str) -> Path:
    job_dir = Path(settings.UPLOAD_DIR) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def get_output_path(job_id: str) -> Path:
    job_dir = Path(settings.OUTPUT_DIR) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


async def _save_single_pdf(
    file: UploadFile,
    destination: Path,
) -> Path:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_size = 0

    with open(destination, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)

            if not chunk:
                break

            total_size += len(chunk)

            if total_size > max_size_bytes:
                if destination.exists():
                    os.remove(destination)

                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
                )

            buffer.write(chunk)

    with open(destination, "rb") as f:
        header = f.read(5)

    if header != b"%PDF-":
        os.remove(destination)
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file.",
        )

    return destination


async def save_uploaded_pdf(file: UploadFile, job_id: str) -> Path:
    upload_dir = get_upload_path(job_id)
    destination = upload_dir / "input.pdf"

    return await _save_single_pdf(file=file, destination=destination)


async def save_uploaded_pdfs(files: List[UploadFile], job_id: str) -> List[Path]:
    if len(files) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least two PDF files are required.",
        )

    upload_dir = get_upload_path(job_id)

    saved_paths: List[Path] = []

    for index, file in enumerate(files, start=1):
        destination = upload_dir / f"input_{index}.pdf"
        saved_path = await _save_single_pdf(file=file, destination=destination)
        saved_paths.append(saved_path)

    return saved_paths