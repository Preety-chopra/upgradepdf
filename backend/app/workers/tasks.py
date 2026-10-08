from pathlib import Path

from app.core.config import settings
from app.services.job_service import (
    mark_job_completed,
    mark_job_failed,
    mark_job_processing,
    purge_expired_jobs,
)
from app.services.pdf_service import (
    compress_pdf,
    delete_pages,
    extract_pages,
    merge_pdfs,
    reorder_pdf,
    rotate_pdf,
)
from app.workers.celery_app import celery_app


@celery_app.task(name="compress_pdf_task")
def compress_pdf_task(job_id: str, quality: str):
    try:
        mark_job_processing(job_id)

        input_path = Path(settings.UPLOAD_DIR) / job_id / "input.pdf"
        output_path = Path(settings.OUTPUT_DIR) / job_id / "compressed.pdf"

        result_path = compress_pdf(
            input_path=input_path,
            output_path=output_path,
            quality=quality,
        )

        mark_job_completed(job_id=job_id, output_filename=result_path.name)

        input_size = input_path.stat().st_size
        output_size = result_path.stat().st_size

        return {
            "job_id": job_id,
            "status": "completed",
            "operation": "compress",
            "quality": quality,
            "filename": result_path.name,
            "input_size_bytes": input_size,
            "output_size_bytes": output_size,
            "savings_percent": round(
                max(0, (input_size - output_size) / input_size * 100), 1
            ),
            "download_url": f"/api/files/download/{job_id}/{result_path.name}",
        }

    except Exception as exc:
        mark_job_failed(job_id=job_id, error_message=str(exc))
        raise


@celery_app.task(name="merge_pdf_task")
def merge_pdf_task(job_id: str):
    try:
        mark_job_processing(job_id)

        upload_dir = Path(settings.UPLOAD_DIR) / job_id
        output_dir = Path(settings.OUTPUT_DIR) / job_id
        output_path = output_dir / "merged.pdf"

        input_paths = sorted(upload_dir.glob("input_*.pdf"))

        result_path = merge_pdfs(
            input_paths=input_paths,
            output_path=output_path,
        )

        mark_job_completed(
            job_id=job_id,
            output_filename=result_path.name,
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "operation": "merge",
            "filename": result_path.name,
            "download_url": f"/api/files/download/{job_id}/{result_path.name}",
        }

    except Exception as exc:
        mark_job_failed(job_id=job_id, error_message=str(exc))
        raise


@celery_app.task(name="split_pdf_task")
def split_pdf_task(job_id: str, pages: str):
    try:
        mark_job_processing(job_id)

        input_path = Path(settings.UPLOAD_DIR) / job_id / "input.pdf"
        output_dir = Path(settings.OUTPUT_DIR) / job_id
        output_path = output_dir / "split_pages.pdf"

        result_path = extract_pages(
            input_path=input_path,
            output_path=output_path,
            pages=pages,
        )

        mark_job_completed(
            job_id=job_id,
            output_filename=result_path.name,
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "operation": "split",
            "filename": result_path.name,
            "download_url": f"/api/files/download/{job_id}/{result_path.name}",
        }

    except Exception as exc:
        mark_job_failed(job_id=job_id, error_message=str(exc))
        raise


@celery_app.task(name="rotate_pdf_task")
def rotate_pdf_task(job_id: str, pages: str, angle: int):
    try:
        mark_job_processing(job_id)

        input_path = Path(settings.UPLOAD_DIR) / job_id / "input.pdf"
        output_dir = Path(settings.OUTPUT_DIR) / job_id
        output_path = output_dir / "rotated.pdf"

        result_path = rotate_pdf(
            input_path=input_path,
            output_path=output_path,
            pages=pages,
            angle=angle,
        )

        mark_job_completed(
            job_id=job_id,
            output_filename=result_path.name,
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "operation": "rotate",
            "filename": result_path.name,
            "download_url": f"/api/files/download/{job_id}/{result_path.name}",
        }

    except Exception as exc:
        mark_job_failed(job_id=job_id, error_message=str(exc))
        raise


@celery_app.task(name="delete_pages_pdf_task")
def delete_pages_pdf_task(job_id: str, pages: str):
    try:
        mark_job_processing(job_id)

        input_path = Path(settings.UPLOAD_DIR) / job_id / "input.pdf"
        output_dir = Path(settings.OUTPUT_DIR) / job_id
        output_path = output_dir / "deleted_pages.pdf"

        result_path = delete_pages(
            input_path=input_path,
            output_path=output_path,
            pages=pages,
        )

        mark_job_completed(
            job_id=job_id,
            output_filename=result_path.name,
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "operation": "delete_pages",
            "filename": result_path.name,
            "download_url": f"/api/files/download/{job_id}/{result_path.name}",
        }

    except Exception as exc:
        mark_job_failed(job_id=job_id, error_message=str(exc))
        raise


@celery_app.task(name="reorder_pdf_task")
def reorder_pdf_task(job_id: str, page_order: str):
    try:
        mark_job_processing(job_id)

        input_path = Path(settings.UPLOAD_DIR) / job_id / "input.pdf"
        output_path = Path(settings.OUTPUT_DIR) / job_id / "reordered.pdf"

        result_path = reorder_pdf(
            input_path=input_path,
            output_path=output_path,
            page_order=page_order,
        )

        mark_job_completed(job_id=job_id, output_filename=result_path.name)

        return {
            "job_id": job_id,
            "status": "completed",
            "operation": "reorder_pages",
            "filename": result_path.name,
            "download_url": f"/api/files/download/{job_id}/{result_path.name}",
        }

    except Exception as exc:
        mark_job_failed(job_id=job_id, error_message=str(exc))
        raise


@celery_app.task(name="purge_expired_jobs_task")
def purge_expired_jobs_task():
    return purge_expired_jobs()
