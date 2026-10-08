import io
import shutil
from pathlib import Path
from typing import Dict, List, Set

import fitz  # PyMuPDF
from PIL import Image


COMPRESSION_PROFILES: Dict[str, dict] = {
    "light": {"max_dimension": 2400, "jpeg_quality": 84},
    "balanced": {"max_dimension": 1800, "jpeg_quality": 72},
    "strong": {"max_dimension": 1200, "jpeg_quality": 55},
}


def _validate_pdf_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are allowed.")


def _encode_compressed_image(
    image_bytes: bytes,
    max_dimension: int,
    jpeg_quality: int,
    source_filter: str = "",
) -> bytes | None:
    """Downsample and encode an embedded image without changing page content."""

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.load()

            largest_dimension = max(image.size)
            if largest_dimension > max_dimension:
                scale = max_dimension / largest_dimension
                image = image.resize(
                    (
                        max(1, round(image.width * scale)),
                        max(1, round(image.height * scale)),
                    ),
                    Image.Resampling.LANCZOS,
                )

            has_alpha = image.mode in {"RGBA", "LA"} or (
                image.mode == "P" and "transparency" in image.info
            )
            output = io.BytesIO()

            if source_filter == "CCITTFaxDecode":
                # CCITT images are monochrome document scans. JPEG is both slow
                # and usually larger for this content, while Group 4 retains the
                # crisp bilevel representation after downsampling.
                image = image.convert("L").convert(
                    "1",
                    dither=Image.Dither.NONE,
                )
                image.save(output, format="TIFF", compression="group4")
            elif has_alpha:
                image.save(output, format="PNG", optimize=True)
            else:
                if image.mode not in {"RGB", "L"}:
                    image = image.convert("RGB")
                image.save(
                    output,
                    format="JPEG",
                    quality=jpeg_quality,
                    optimize=True,
                    progressive=True,
                )

            candidate = output.getvalue()
            if len(candidate) >= len(image_bytes) * 0.95:
                return None

            return candidate
    except (OSError, ValueError):
        # Unsupported image encodings are left untouched. Document-level
        # cleanup can still compress their streams.
        return None


def compress_pdf(input_path: Path, output_path: Path, quality: str) -> Path:
    """Compress a PDF while preserving text, links, forms, and vectors."""

    _validate_pdf_path(input_path)

    if quality not in COMPRESSION_PROFILES:
        raise ValueError("Quality must be one of: light, balanced, strong.")

    profile = COMPRESSION_PROFILES[quality]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    working_path = output_path.with_suffix(".working.pdf")

    try:
        with fitz.open(input_path) as doc:
            if doc.needs_pass:
                raise ValueError(
                    "Password-protected PDFs are not supported for compression."
                )

            if doc.page_count < 1:
                raise ValueError("The PDF does not contain any pages.")

            image_pages: Dict[int, tuple[int, str]] = {}
            for page_number in range(doc.page_count):
                for image in doc.get_page_images(page_number, full=True):
                    xref, soft_mask_xref = image[0], image[1]
                    # Resizing an image independently from its soft mask can
                    # corrupt transparency, so those images are preserved.
                    if xref > 0 and soft_mask_xref == 0:
                        image_pages.setdefault(xref, (page_number, image[8]))

            for xref, (page_number, source_filter) in image_pages.items():
                extracted = doc.extract_image(xref)
                original = extracted.get("image")
                if not original:
                    continue

                replacement = _encode_compressed_image(
                    original,
                    max_dimension=profile["max_dimension"],
                    jpeg_quality=profile["jpeg_quality"],
                    source_filter=source_filter,
                )
                if replacement:
                    page = doc.load_page(page_number)
                    page.replace_image(xref, stream=replacement)

            doc.save(
                working_path,
                garbage=4,
                clean=True,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
                use_objstms=1,
            )

        if working_path.stat().st_size < input_path.stat().st_size:
            working_path.replace(output_path)
        else:
            shutil.copy2(input_path, output_path)
            working_path.unlink(missing_ok=True)

        # Reopen the artifact so corrupt output is never marked successful.
        with fitz.open(output_path) as result:
            if result.page_count < 1:
                raise ValueError("Compression produced an invalid PDF.")

        return output_path
    finally:
        working_path.unlink(missing_ok=True)


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


def _parse_page_order(page_order: str, total_pages: int) -> List[int]:
    """Validate a one-based page permutation and return zero-based indexes."""

    if not page_order or not page_order.strip():
        raise ValueError("Page order is required.")

    parts = [part.strip() for part in page_order.split(",")]
    if any(not part.isdigit() for part in parts):
        raise ValueError("Page order must be a comma-separated list of page numbers.")

    ordered_pages = [int(part) for part in parts]
    expected_pages = set(range(1, total_pages + 1))

    if len(ordered_pages) != total_pages or set(ordered_pages) != expected_pages:
        raise ValueError(
            f"Page order must include every page from 1 to {total_pages} exactly once."
        )

    return [page_number - 1 for page_number in ordered_pages]


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


def reorder_pdf(input_path: Path, output_path: Path, page_order: str) -> Path:
    """Save every page in the exact order requested by the user."""

    _validate_pdf_path(input_path)

    with fitz.open(input_path) as document:
        if document.needs_pass:
            raise ValueError("Password-protected PDFs are not supported.")
        if document.page_count < 1:
            raise ValueError("The PDF does not contain any pages.")

        ordered_indexes = _parse_page_order(page_order, document.page_count)
        document.select(ordered_indexes)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        document.save(output_path, garbage=3, deflate=True)

    with fitz.open(output_path) as result:
        if result.page_count != len(ordered_indexes):
            raise ValueError("Reordering produced an invalid PDF.")

    return output_path
