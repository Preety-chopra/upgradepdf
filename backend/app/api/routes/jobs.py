from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.job import JobOperation
from app.schemas.job import JobResponse
from app.services.job_service import build_download_url, get_job_by_id, purge_expired_jobs

router = APIRouter()


@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
):
    job = get_job_by_id(db=db, job_id=job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    response = JobResponse.model_validate(job)
    response.download_url = build_download_url(job)

    if job.operation == JobOperation.COMPRESS:
        input_path = Path(settings.UPLOAD_DIR) / job.id / "input.pdf"
        output_path = (
            Path(settings.OUTPUT_DIR) / job.id / job.output_filename
            if job.output_filename
            else None
        )

        if input_path.exists():
            response.input_size_bytes = input_path.stat().st_size

        if output_path and output_path.exists():
            response.output_size_bytes = output_path.stat().st_size

        if response.input_size_bytes and response.output_size_bytes is not None:
            response.savings_percent = round(
                max(
                    0,
                    (response.input_size_bytes - response.output_size_bytes)
                    / response.input_size_bytes
                    * 100,
                ),
                1,
            )

    return response


@router.post("/purge/manual")
def manual_purge():
    """
    Manual purge trigger for development/admin testing.

    In production, protect this endpoint with admin authentication.
    """

    return purge_expired_jobs()