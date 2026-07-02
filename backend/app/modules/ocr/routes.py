from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from .schemas import OcrJobCreateResponse, OcrLanguagesResponse, OcrStatusResponse
from .service import SUPPORTED_LANGUAGES, installed_tesseract_languages, parse_language_codes
from .storage import (
    create_job_id,
    get_job_dir,
    public_status_payload,
    read_status,
    safe_filename,
    save_ocr_upload,
    utc_now,
    write_status,
)
from .tasks import process_ocr_job

router = APIRouter(prefix="/api/ocr", tags=["OCR"])
OCR_QUEUE = os.getenv("OCR_QUEUE", "ocr")


@router.get("/languages", response_model=OcrLanguagesResponse)
def get_ocr_languages() -> OcrLanguagesResponse:
    installed = installed_tesseract_languages()
    return OcrLanguagesResponse(
        supported=[
            {"code": code, "label": label, "installed": code in installed if installed else False}
            for code, label in SUPPORTED_LANGUAGES.items()
        ],
        installed=sorted(installed),
    )


@router.post("/jobs", response_model=OcrJobCreateResponse)
async def create_ocr_job(
    file: UploadFile = File(...),
    language: str = Form("eng"),
    export_text: bool = Form(True),
    deskew: bool = Form(True),
    rotate_pages: bool = Form(True),
    force_ocr: bool = Form(False),
    timeout_seconds: int = Form(1200),
) -> OcrJobCreateResponse:
    try:
        language_codes = parse_language_codes(language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = create_job_id()
    job_dir = get_job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    source_path = await save_ocr_upload(file, job_dir)
    original_name = safe_filename(file.filename, source_path.name)
    joined_language = "+".join(language_codes)

    write_status(
        job_id,
        {
            "job_id": job_id,
            "status": "queued",
            "percent": 0,
            "message": "OCR job queued.",
            "filename": original_name,
            "input_filename": source_path.name,
            "language": joined_language,
            "export_text": export_text,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        },
    )

    payload = {
        "input_filename": source_path.name,
        "language": joined_language,
        "export_text": export_text,
        "deskew": deskew,
        "rotate_pages": rotate_pages,
        "force_ocr": force_ocr,
        "timeout_seconds": timeout_seconds,
    }
    process_ocr_job.apply_async(args=[job_id, payload], queue=OCR_QUEUE)

    return OcrJobCreateResponse(
        job_id=job_id,
        status="queued",
        status_url=f"/api/ocr/jobs/{job_id}",
        pdf_download_url=f"/api/ocr/jobs/{job_id}/download?file_type=pdf",
        text_download_url=f"/api/ocr/jobs/{job_id}/download?file_type=text" if export_text else None,
    )


@router.get("/jobs/{job_id}", response_model=OcrStatusResponse)
def get_ocr_job_status(job_id: str) -> OcrStatusResponse:
    return OcrStatusResponse(**public_status_payload(read_status(job_id)))


@router.get("/jobs/{job_id}/download")
def download_ocr_output(
    job_id: str,
    file_type: str = Query("pdf", pattern="^(pdf|text)$"),
) -> FileResponse:
    status = read_status(job_id)
    if status.get("status") != "completed":
        raise HTTPException(status_code=409, detail="OCR output is not ready yet.")

    job_dir = get_job_dir(job_id)
    if file_type == "pdf":
        relative_path = status.get("output_pdf")
        if not relative_path:
            raise HTTPException(status_code=404, detail="Searchable PDF output not found.")
        path = job_dir / relative_path
        media_type = "application/pdf"
        suffix = "searchable.pdf"
    else:
        relative_path = status.get("output_text")
        if not relative_path:
            raise HTTPException(status_code=404, detail="Text export was not requested or was not created.")
        path = job_dir / relative_path
        media_type = "text/plain; charset=utf-8"
        suffix = "ocr.txt"

    if not path.exists():
        raise HTTPException(status_code=404, detail="OCR output file is missing.")

    original = Path(status.get("filename") or "ocr_output").stem
    filename = f"{original}_{suffix}"
    return FileResponse(path=path, filename=filename, media_type=media_type)
