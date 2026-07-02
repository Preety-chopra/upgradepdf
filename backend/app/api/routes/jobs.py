from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import JobStatus
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

    return response


@router.post("/purge/manual")
def manual_purge():
    """
    Manual purge trigger for development/admin testing.

    In production, protect this endpoint with admin authentication.
    """

    return purge_expired_jobs()