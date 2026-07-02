from pathlib import Path

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.job import JobStatus
from app.services.job_service import get_job_by_id
from app.workers.celery_app import celery_app

router = APIRouter()


@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    task = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": task.status,
    }

    if task.successful():
        response["result"] = task.result

    elif task.failed():
        response["error"] = str(task.result)

    return response


@router.get("/download/{job_id}/{filename}")
def download_processed_file(
    job_id: str,
    filename: str,
    db: Session = Depends(get_db),
):
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    job = get_job_by_id(db=db, job_id=job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    if job.status == JobStatus.PURGED:
        raise HTTPException(
            status_code=410,
            detail="This file has been deleted as per the 60-minute retention policy.",
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"File is not ready. Current job status: {job.status}",
        )

    if job.output_filename != filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid output file requested.",
        )

    file_path = Path(settings.OUTPUT_DIR) / job_id / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found or already deleted.",
        )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
    )