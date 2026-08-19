from __future__ import annotations

import os
from typing import Any

from celery.exceptions import SoftTimeLimitExceeded

from app.workers.celery_app import celery_app

from .service import OcrProcessingError, OcrTimeoutError, parse_language_codes, process_ocr_file
from .storage import update_status, utc_now

OCR_SOFT_TIME_LIMIT = int(os.getenv("OCR_SOFT_TIME_LIMIT", "1500"))
OCR_HARD_TIME_LIMIT = int(os.getenv("OCR_HARD_TIME_LIMIT", "1800"))

@celery_app.task(
    name="app.modules.ocr.tasks.process_ocr_job",
    bind=True,
    acks_late=True,
    soft_time_limit=OCR_SOFT_TIME_LIMIT,
    time_limit=OCR_HARD_TIME_LIMIT,
)
def process_ocr_job(self: Any, job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        process_ocr_file(
            job_id=job_id,
            input_filename=payload["input_filename"],
            language_codes=parse_language_codes(payload.get("language", "eng")),
            export_text=bool(payload.get("export_text", True)),
            deskew=bool(payload.get("deskew", True)),
            rotate_pages=bool(payload.get("rotate_pages", True)),
            force_ocr=bool(payload.get("force_ocr", False)),
            timeout_seconds=int(payload.get("timeout_seconds") or 0) or None,
        )
        return {"job_id": job_id, "status": "completed"}
    except SoftTimeLimitExceeded as exc:
        update_status(
            job_id,
            status="timeout",
            percent=100,
            message="OCR stopped because worker soft time limit was reached.",
            error=str(exc),
            completed_at=utc_now(),
        )
        raise
    except OcrTimeoutError as exc:
        update_status(
            job_id,
            status="timeout",
            percent=100,
            message="OCR timed out.",
            error=str(exc),
            completed_at=utc_now(),
        )
        raise
    except (OcrProcessingError, ValueError) as exc:
        update_status(
            job_id,
            status="failed",
            percent=100,
            message="OCR failed.",
            error=str(exc),
            completed_at=utc_now(),
        )
        raise
    except Exception as exc:
        update_status(
            job_id,
            status="failed",
            percent=100,
            message="OCR failed due to an unexpected error.",
            error=str(exc),
            completed_at=utc_now(),
        )
        raise
