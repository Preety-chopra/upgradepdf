from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .security import save_upload_file
from .service import (
    images_to_pdf,
    office_to_pdf,
    pdf_to_csv_or_zip,
    pdf_to_docx,
    pdf_to_jpg_zip,
    pdf_to_xlsx,
)

router = APIRouter(prefix="/api/conversions", tags=["Conversion Tools"])

PDF_EXT = {".pdf"}
IMAGE_EXT = {".jpg", ".jpeg", ".png"}
WORD_EXT = {".doc", ".docx", ".odt", ".rtf"}
EXCEL_EXT = {".xls", ".xlsx", ".xlsm", ".ods", ".csv"}


def _response(path: Path, media_type: str, tmp: tempfile.TemporaryDirectory, filename: str | None = None) -> FileResponse:
    return FileResponse(
        path=path,
        filename=filename or path.name,
        media_type=media_type,
        background=BackgroundTask(tmp.cleanup),
    )


@router.post("/pdf-to-jpg")
async def convert_pdf_to_jpg(
    file: UploadFile = File(...),
    dpi: int = Form(200),
    quality: int = Form(90),
):
    tmp = tempfile.TemporaryDirectory(prefix="conv_pdf_jpg_")
    try:
        base = Path(tmp.name)
        input_pdf = await save_upload_file(file, base / "input", PDF_EXT)
        output_zip = pdf_to_jpg_zip(input_pdf, base / "output", dpi=dpi, quality=quality)
        return _response(output_zip, "application/zip", tmp)
    except Exception:
        tmp.cleanup()
        raise


@router.post("/images-to-pdf")
async def convert_images_to_pdf(files: list[UploadFile] = File(...)):
    tmp = tempfile.TemporaryDirectory(prefix="conv_images_pdf_")
    try:
        base = Path(tmp.name)
        image_paths = [await save_upload_file(file, base / "input", IMAGE_EXT) for file in files]
        output_pdf = images_to_pdf(image_paths, base / "output" / "converted_images.pdf")
        return _response(output_pdf, "application/pdf", tmp)
    except Exception:
        tmp.cleanup()
        raise


@router.post("/word-to-pdf")
async def convert_word_to_pdf(file: UploadFile = File(...)):
    tmp = tempfile.TemporaryDirectory(prefix="conv_word_pdf_")
    try:
        base = Path(tmp.name)
        input_doc = await save_upload_file(file, base / "input", WORD_EXT)
        output_pdf = office_to_pdf(input_doc, base / "output")
        return _response(output_pdf, "application/pdf", tmp, filename=f"{input_doc.stem}.pdf")
    except Exception:
        tmp.cleanup()
        raise


@router.post("/excel-to-pdf")
async def convert_excel_to_pdf(file: UploadFile = File(...)):
    tmp = tempfile.TemporaryDirectory(prefix="conv_excel_pdf_")
    try:
        base = Path(tmp.name)
        input_sheet = await save_upload_file(file, base / "input", EXCEL_EXT)
        output_pdf = office_to_pdf(input_sheet, base / "output")
        return _response(output_pdf, "application/pdf", tmp, filename=f"{input_sheet.stem}.pdf")
    except Exception:
        tmp.cleanup()
        raise


@router.post("/pdf-to-word")
async def convert_pdf_to_word(
    file: UploadFile = File(...),
    mode: Literal["auto", "layout", "text", "image", "ocr"] = Form("auto"),
    dpi: int = Form(180),
):
    tmp = tempfile.TemporaryDirectory(prefix="conv_pdf_word_")
    try:
        base = Path(tmp.name)
        input_pdf = await save_upload_file(file, base / "input", PDF_EXT)
        output_docx = pdf_to_docx(
            input_pdf,
            base / "output" / f"{input_pdf.stem}.docx",
            base / "work",
            mode=mode,
            dpi=dpi,
        )
        return _response(
            output_docx,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            tmp,
        )
    except Exception:
        tmp.cleanup()
        raise


@router.post("/pdf-to-data")
async def convert_pdf_to_data(
    file: UploadFile = File(...),
    output_format: Literal["xlsx", "csv"] = Query("xlsx", alias="format"),
):
    tmp = tempfile.TemporaryDirectory(prefix="conv_pdf_data_")
    try:
        base = Path(tmp.name)
        input_pdf = await save_upload_file(file, base / "input", PDF_EXT)
        if output_format == "xlsx":
            output_xlsx = pdf_to_xlsx(input_pdf, base / "output" / f"{input_pdf.stem}_tables.xlsx")
            return _response(
                output_xlsx,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                tmp,
            )

        output_csv = pdf_to_csv_or_zip(input_pdf, base / "output")
        media_type = "application/zip" if output_csv.suffix.lower() == ".zip" else "text/csv"
        return _response(output_csv, media_type, tmp)
    except Exception:
        tmp.cleanup()
        raise
