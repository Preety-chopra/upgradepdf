from typing import List, Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import JobOperation
from app.services.file_service import (
    create_job_id,
    save_uploaded_pdf,
    save_uploaded_pdfs,
)
from app.services.job_service import create_job, set_task_id
from app.workers.tasks import (
    compress_pdf_task,
    delete_pages_pdf_task,
    merge_pdf_task,
    rotate_pdf_task,
    split_pdf_task,
)

router = APIRouter()


@router.post("/compress")
async def compress_pdf_api(
    file: UploadFile = File(...),
    quality: Literal["light", "balanced", "strong"] = Form("balanced"),
    db: Session = Depends(get_db),
):
    job_id = create_job_id()

    await save_uploaded_pdf(file=file, job_id=job_id)

    create_job(
        db=db,
        job_id=job_id,
        operation=JobOperation.COMPRESS,
        input_filename=file.filename,
    )

    task = compress_pdf_task.delay(job_id, quality)
    set_task_id(db=db, job_id=job_id, task_id=task.id)

    return {
        "message": "Compression job started.",
        "job_id": job_id,
        "task_id": task.id,
        "quality": quality,
        "job_status_url": f"/api/jobs/{job_id}",
        "task_status_url": f"/api/files/status/{task.id}",
    }


@router.post("/merge")
async def merge_pdf(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    job_id = create_job_id()

    await save_uploaded_pdfs(files=files, job_id=job_id)

    create_job(
        db=db,
        job_id=job_id,
        operation=JobOperation.MERGE,
        input_filename=f"{len(files)} PDF files",
    )

    task = merge_pdf_task.delay(job_id)

    set_task_id(
        db=db,
        job_id=job_id,
        task_id=task.id,
    )

    return {
        "message": "Merge job started.",
        "job_id": job_id,
        "task_id": task.id,
        "job_status_url": f"/api/jobs/{job_id}",
        "task_status_url": f"/api/files/status/{task.id}",
    }


@router.post("/split")
async def split_pdf(
    file: UploadFile = File(...),
    pages: str = Form(...),
    db: Session = Depends(get_db),
):
    job_id = create_job_id()

    await save_uploaded_pdf(file=file, job_id=job_id)

    create_job(
        db=db,
        job_id=job_id,
        operation=JobOperation.SPLIT,
        input_filename=file.filename,
    )

    task = split_pdf_task.delay(job_id, pages)

    set_task_id(
        db=db,
        job_id=job_id,
        task_id=task.id,
    )

    return {
        "message": "Split job started.",
        "job_id": job_id,
        "task_id": task.id,
        "pages": pages,
        "job_status_url": f"/api/jobs/{job_id}",
        "task_status_url": f"/api/files/status/{task.id}",
    }


@router.post("/rotate")
async def rotate_pdf_api(
    file: UploadFile = File(...),
    pages: str = Form("all"),
    angle: int = Form(...),
    db: Session = Depends(get_db),
):
    job_id = create_job_id()

    await save_uploaded_pdf(file=file, job_id=job_id)

    create_job(
        db=db,
        job_id=job_id,
        operation=JobOperation.ROTATE,
        input_filename=file.filename,
    )

    task = rotate_pdf_task.delay(job_id, pages, angle)

    set_task_id(
        db=db,
        job_id=job_id,
        task_id=task.id,
    )

    return {
        "message": "Rotate job started.",
        "job_id": job_id,
        "task_id": task.id,
        "pages": pages,
        "angle": angle,
        "job_status_url": f"/api/jobs/{job_id}",
        "task_status_url": f"/api/files/status/{task.id}",
    }


@router.post("/delete-pages")
async def delete_pages_pdf_api(
    file: UploadFile = File(...),
    pages: str = Form(...),
    db: Session = Depends(get_db),
):
    job_id = create_job_id()

    await save_uploaded_pdf(file=file, job_id=job_id)

    create_job(
        db=db,
        job_id=job_id,
        operation=JobOperation.DELETE_PAGES,
        input_filename=file.filename,
    )

    task = delete_pages_pdf_task.delay(job_id, pages)

    set_task_id(
        db=db,
        job_id=job_id,
        task_id=task.id,
    )

    return {
        "message": "Delete pages job started.",
        "job_id": job_id,
        "task_id": task.id,
        "pages": pages,
        "job_status_url": f"/api/jobs/{job_id}",
        "task_status_url": f"/api/files/status/{task.id}",
    }