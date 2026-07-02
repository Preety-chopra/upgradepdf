import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.job import Job, JobOperation, JobStatus


def create_job(
    db: Session,
    job_id: str,
    operation: JobOperation,
    input_filename: Optional[str] = None,
) -> Job:
    job = Job(
        id=job_id,
        operation=operation,
        status=JobStatus.PENDING,
        input_filename=input_filename,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def set_task_id(
    db: Session,
    job_id: str,
    task_id: str,
) -> Optional[Job]:
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        return None

    job.task_id = task_id
    db.commit()
    db.refresh(job)

    return job


def mark_job_processing(job_id: str) -> None:
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if job:
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            db.commit()

    finally:
        db.close()


def mark_job_completed(
    job_id: str,
    output_filename: str,
) -> None:
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if job:
            job.status = JobStatus.COMPLETED
            job.output_filename = output_filename
            job.completed_at = datetime.utcnow()
            db.commit()

    finally:
        db.close()


def mark_job_failed(
    job_id: str,
    error_message: str,
) -> None:
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if job:
            job.status = JobStatus.FAILED
            job.error_message = error_message[:2000]
            job.completed_at = datetime.utcnow()
            db.commit()

    finally:
        db.close()


def get_job_by_id(
    db: Session,
    job_id: str,
) -> Optional[Job]:
    return db.query(Job).filter(Job.id == job_id).first()


def build_download_url(job: Job) -> Optional[str]:
    if job.status != JobStatus.COMPLETED:
        return None

    if not job.output_filename:
        return None

    return f"/api/files/download/{job.id}/{job.output_filename}"


def purge_expired_jobs() -> dict:
    """
    Deletes upload/output folders for completed or failed jobs
    after FILE_RETENTION_MINUTES.

    This does not delete the DB job record.
    It only marks the job as PURGED.
    """

    db = SessionLocal()
    purged_count = 0

    try:
        expiry_time = datetime.utcnow() - timedelta(
            minutes=settings.FILE_RETENTION_MINUTES
        )

        expired_jobs = (
            db.query(Job)
            .filter(Job.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]))
            .filter(Job.completed_at.isnot(None))
            .filter(Job.completed_at <= expiry_time)
            .all()
        )

        for job in expired_jobs:
            upload_dir = Path(settings.UPLOAD_DIR) / job.id
            output_dir = Path(settings.OUTPUT_DIR) / job.id

            if upload_dir.exists():
                shutil.rmtree(upload_dir, ignore_errors=True)

            if output_dir.exists():
                shutil.rmtree(output_dir, ignore_errors=True)

            job.status = JobStatus.PURGED
            job.purged_at = datetime.utcnow()
            purged_count += 1

        db.commit()

        return {
            "status": "completed",
            "message": "Purge task completed. Count only includes jobs newly changed to purged.",
            "purged_count": purged_count,
        }

    finally:
        db.close()