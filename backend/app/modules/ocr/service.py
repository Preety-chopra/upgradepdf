from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF
from PIL import Image, ImageOps

from .storage import IMAGE_EXTENSIONS, PDF_EXTENSIONS, get_job_dir, update_status, utc_now

Image.MAX_IMAGE_PIXELS = int(os.getenv("OCR_MAX_IMAGE_PIXELS", "180000000"))

SUPPORTED_LANGUAGES: dict[str, str] = {
    "eng": "English",
    "hin": "Hindi",
    "ben": "Bengali",
    "tam": "Tamil",
    "tel": "Telugu",
    "mar": "Marathi",
    "guj": "Gujarati",
    "kan": "Kannada",
    "mal": "Malayalam",
    "pan": "Punjabi",
    "urd": "Urdu",
}

DEFAULT_TIMEOUT_SECONDS = int(os.getenv("OCR_DEFAULT_TIMEOUT_SECONDS", "1200"))
MAX_TIMEOUT_SECONDS = int(os.getenv("OCR_MAX_TIMEOUT_SECONDS", "1800"))
MAX_PAGES = int(os.getenv("OCR_MAX_PAGES", "150"))
OCR_JOBS_PER_FILE = int(os.getenv("OCR_OCRMYPDF_JOBS", "1"))


class OcrProcessingError(Exception):
    pass


class OcrTimeoutError(OcrProcessingError):
    pass


def parse_language_codes(language: str | Iterable[str] | None) -> list[str]:
    if language is None:
        raw_codes = ["eng"]
    elif isinstance(language, str):
        raw_codes = [part.strip() for part in language.replace(",", "+").split("+")]
    else:
        raw_codes = [str(part).strip() for part in language]

    codes: list[str] = []
    for code in raw_codes:
        if not code:
            continue
        if code not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported OCR language: {code}")
        if code not in codes:
            codes.append(code)

    return codes or ["eng"]


def installed_tesseract_languages() -> set[str]:
    if not shutil.which("tesseract"):
        return set()
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception:
        return set()

    languages: set[str] = set()
    for line in (result.stdout + "\n" + result.stderr).splitlines():
        line = line.strip()
        if not line or line.lower().startswith("list of"):
            continue
        if " " in line or ":" in line:
            continue
        languages.add(line)
    return languages


def require_ocr_tools(language_codes: list[str]) -> None:
    missing_tools = [tool for tool in ("ocrmypdf", "tesseract") if not shutil.which(tool)]
    if missing_tools:
        raise OcrProcessingError(
            "Missing OCR system tools: " + ", ".join(missing_tools) + ". Install OCR packages in the API/worker image."
        )

    installed = installed_tesseract_languages()
    if installed:
        missing_languages = [code for code in language_codes if code not in installed]
        if missing_languages:
            raise OcrProcessingError(
                "Missing Tesseract language data: "
                + ", ".join(missing_languages)
                + ". Install the matching tesseract-ocr-* package."
            )


def clamp_timeout(timeout_seconds: int | None) -> int:
    if not timeout_seconds:
        return DEFAULT_TIMEOUT_SECONDS
    return max(60, min(int(timeout_seconds), MAX_TIMEOUT_SECONDS))


def ensure_pdf_input(source_path: Path, work_dir: Path) -> Path:
    extension = source_path.suffix.lower()
    if extension in PDF_EXTENSIONS:
        return source_path
    if extension not in IMAGE_EXTENSIONS:
        raise OcrProcessingError("OCR input must be a PDF or image file.")

    output_pdf = work_dir / "input_from_image.pdf"
    work_dir.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(source_path) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode in ("RGBA", "LA"):
                background = Image.new("RGB", image.size, "white")
                background.paste(image, mask=image.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
            image.save(output_pdf, "PDF", resolution=300.0)
    except Exception as exc:
        raise OcrProcessingError(f"Unable to prepare image for OCR: {exc}") from exc
    return output_pdf


def count_pdf_pages(pdf_path: Path) -> int:
    try:
        with fitz.open(pdf_path) as document:
            return document.page_count
    except Exception as exc:
        raise OcrProcessingError(f"Unable to read input PDF: {exc}") from exc


def extract_text_from_searchable_pdf(pdf_path: Path, text_path: Path) -> Path:
    text_path.parent.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    with fitz.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            parts.append(f"\n\n--- Page {page_number} ---\n")
            parts.append(page.get_text("text") or "")
    text_path.write_text("".join(parts).strip() + "\n", encoding="utf-8")
    return text_path


def run_ocr_command(
    *,
    job_id: str,
    command: list[str],
    timeout_seconds: int,
    log_path: Path,
) -> str:
    started = time.monotonic()
    last_percent = 15
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT, text=True)

        while process.poll() is None:
            elapsed = time.monotonic() - started
            if elapsed > timeout_seconds:
                process.kill()
                process.wait(timeout=10)
                raise OcrTimeoutError(f"OCR timed out after {timeout_seconds} seconds.")

            estimated_percent = min(90, 15 + int((elapsed / timeout_seconds) * 70))
            if estimated_percent > last_percent:
                last_percent = estimated_percent
                update_status(
                    job_id,
                    status="running",
                    percent=estimated_percent,
                    message=f"OCR is running... elapsed {int(elapsed)} seconds.",
                )
            time.sleep(2)

        exit_code = process.returncode

    log_text = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
    if exit_code != 0:
        raise OcrProcessingError(log_text.strip() or f"OCRmyPDF failed with exit code {exit_code}.")
    return log_text


def process_ocr_file(
    *,
    job_id: str,
    input_filename: str,
    language_codes: list[str],
    export_text: bool,
    deskew: bool,
    rotate_pages: bool,
    force_ocr: bool,
    timeout_seconds: int | None,
) -> None:
    job_dir = get_job_dir(job_id)
    source_path = job_dir / "input" / input_filename
    if not source_path.exists():
        raise OcrProcessingError("Uploaded source file is missing.")

    timeout = clamp_timeout(timeout_seconds)
    language_codes = parse_language_codes(language_codes)
    language = "+".join(language_codes)

    update_status(job_id, status="running", percent=5, message="Checking OCR tools and input file.", language=language)
    require_ocr_tools(language_codes)

    work_dir = job_dir / "work"
    output_dir = job_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    input_pdf = ensure_pdf_input(source_path, work_dir)

    page_count = count_pdf_pages(input_pdf)
    if page_count < 1:
        raise OcrProcessingError("Input PDF has no pages.")
    if page_count > MAX_PAGES:
        raise OcrProcessingError(
            f"Input has {page_count} pages. Current OCR limit is {MAX_PAGES} pages. Split the PDF or increase OCR_MAX_PAGES."
        )

    update_status(
        job_id,
        status="running",
        percent=12,
        page_count=page_count,
        message=f"Prepared {page_count} page(s). Starting OCR.",
    )

    output_pdf = output_dir / f"{source_path.stem}_searchable.pdf"
    output_text = output_dir / f"{source_path.stem}_ocr.txt"
    log_path = job_dir / "ocr.log"

    command = [
        "ocrmypdf",
        "--jobs",
        str(max(1, OCR_JOBS_PER_FILE)),
        "--language",
        language,
        "--output-type",
        "pdf",
        "--optimize",
        "1",
        "--pdf-renderer",
        "auto",
    ]

    if deskew:
        command.append("--deskew")
    if rotate_pages:
        command.append("--rotate-pages")
    if force_ocr:
        command.append("--force-ocr")
    else:
        command.append("--skip-text")
    if export_text:
        command.extend(["--sidecar", str(output_text)])

    command.extend([str(input_pdf), str(output_pdf)])

    run_ocr_command(job_id=job_id, command=command, timeout_seconds=timeout, log_path=log_path)

    if not output_pdf.exists() or output_pdf.stat().st_size == 0:
        raise OcrProcessingError("OCR completed but searchable PDF was not created.")

    if export_text and (not output_text.exists() or output_text.stat().st_size == 0):
        extract_text_from_searchable_pdf(output_pdf, output_text)

    update_status(
        job_id,
        status="completed",
        percent=100,
        message="OCR completed. Searchable PDF is ready.",
        output_pdf=str(output_pdf.relative_to(job_dir)),
        output_text=str(output_text.relative_to(job_dir)) if export_text and output_text.exists() else None,
        completed_at=utc_now(),
        error=None,
    )
