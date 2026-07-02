from pathlib import Path
from typing import List, Set

import fitz  # PyMuPDF


def _validate_pdf_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are allowed.")


def _parse_pages(pages: str, total_pages: int) -> List[int]:
    """
    Converts user page input into zero-based page indexes.

    Examples:
    "1,3,5"   -> [0, 2, 4]
    "1-3"     -> [0, 1, 2]
    "1,3-5"   -> [0, 2, 3, 4]
    "all"     -> all pages
    """

    if not pages:
        raise ValueError("Pages value is required.")

    pages = pages.strip().lower()

    if pages == "all":
        return list(range(total_pages))

    selected_pages: Set[int] = set()

    parts = pages.split(",")

    for part in parts:
        part = part.strip()

        if not part:
            continue

        if "-" in part:
            start_text, end_text = part.split("-", 1)

            if not start_text.isdigit() or not end_text.isdigit():
                raise ValueError(f"Invalid page range: {part}")

            start = int(start_text)
            end = int(end_text)

            if start > end:
                raise ValueError(f"Invalid page range: {part}")

            for page_number in range(start, end + 1):
                if page_number < 1 or page_number > total_pages:
                    raise ValueError(
                        f"Page {page_number} is outside document range 1-{total_pages}."
                    )

                selected_pages.add(page_number - 1)

        else:
            if not part.isdigit():
                raise ValueError(f"Invalid page number: {part}")

            page_number = int(part)

            if page_number < 1 or page_number > total_pages:
                raise ValueError(
                    f"Page {page_number} is outside document range 1-{total_pages}."
                )

            selected_pages.add(page_number - 1)

    if not selected_pages:
        raise ValueError("No valid pages selected.")

    return sorted(selected_pages)


def merge_pdfs(input_paths: List[Path], output_path: Path) -> Path:
    """
    Merge multiple PDFs into one PDF.
    """

    if len(input_paths) < 2:
        raise ValueError("At least two PDF files are required for merge.")

    output_doc = fitz.open()

    try:
        for input_path in input_paths:
            _validate_pdf_path(input_path)

            with fitz.open(input_path) as source_doc:
                output_doc.insert_pdf(source_doc)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_doc.save(output_path)
        return output_path

    finally:
        output_doc.close()


def extract_pages(input_path: Path, output_path: Path, pages: str) -> Path:
    """
    Extract selected pages from a PDF and save as a new PDF.
    This works as our first split feature.
    """

    _validate_pdf_path(input_path)

    with fitz.open(input_path) as source_doc:
        total_pages = source_doc.page_count
        selected_indexes = _parse_pages(pages, total_pages)

        output_doc = fitz.open()

        try:
            for page_index in selected_indexes:
                output_doc.insert_pdf(
                    source_doc,
                    from_page=page_index,
                    to_page=page_index,
                )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_doc.save(output_path)
            return output_path

        finally:
            output_doc.close()


def rotate_pdf(input_path: Path, output_path: Path, pages: str, angle: int) -> Path:
    """
    Rotate selected pages.

    Allowed angles:
    90, 180, 270, -90, -180, -270
    """

    _validate_pdf_path(input_path)

    if angle not in [90, 180, 270, -90, -180, -270]:
        raise ValueError("Angle must be one of: 90, 180, 270, -90, -180, -270.")

    with fitz.open(input_path) as doc:
        selected_indexes = _parse_pages(pages, doc.page_count)

        for page_index in selected_indexes:
            page = doc[page_index]
            current_rotation = page.rotation
            new_rotation = (current_rotation + angle) % 360
            page.set_rotation(new_rotation)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)
        return output_path


def delete_pages(input_path: Path, output_path: Path, pages: str) -> Path:
    """
    Delete selected pages and save the remaining pages as a new PDF.
    """

    _validate_pdf_path(input_path)

    with fitz.open(input_path) as source_doc:
        total_pages = source_doc.page_count
        delete_indexes = set(_parse_pages(pages, total_pages))

        keep_indexes = [
            page_index
            for page_index in range(total_pages)
            if page_index not in delete_indexes
        ]

        if not keep_indexes:
            raise ValueError("Cannot delete all pages. At least one page must remain.")

        output_doc = fitz.open()

        try:
            for page_index in keep_indexes:
                output_doc.insert_pdf(
                    source_doc,
                    from_page=page_index,
                    to_page=page_index,
                )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_doc.save(output_path)
            return output_path

        finally:
            output_doc.close()