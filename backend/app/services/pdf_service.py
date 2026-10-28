import io
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps
from pytesseract import Output


COMPRESSION_PROFILES: Dict[str, dict] = {
    "light": {"max_dimension": 2400, "jpeg_quality": 84, "image_scale": 0.95},
    "balanced": {"max_dimension": 1800, "jpeg_quality": 72, "image_scale": 0.85},
    "strong": {"max_dimension": 1200, "jpeg_quality": 55, "image_scale": 0.70},
}

OPTIMIZATION_OPTION_NAMES = {
    "vectorize_text",
    "invert_colors",
    "deskew",
    "whiten_background",
    "darken_text",
    "enhance_font_weight",
}


@dataclass(frozen=True)
class PdfComparisonResult:
    output_path: Path
    summary: dict


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
    image_scale: float = 1.0,
    original_size: int | None = None,
) -> bytes | None:
    """Downsample and encode an embedded image without changing page content."""

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.load()

            largest_dimension = max(image.size)
            # Absolute limits alone leave ordinary screen-sized scans unchanged.
            # Apply a graduated reduction too, without shrinking small logos.
            target_dimension = min(
                max_dimension, max(256, round(largest_dimension * image_scale))
            )
            if largest_dimension > target_dimension:
                scale = target_dimension / largest_dimension
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
            candidates = []
            output = io.BytesIO()

            if source_filter == "CCITTFaxDecode" or image.mode == "1":
                # CCITT images are monochrome document scans. JPEG is both slow
                # and usually larger for this content, while Group 4 retains the
                # crisp bilevel representation after downsampling.
                image = image.convert("L").convert(
                    "1",
                    dither=Image.Dither.NONE,
                )
                image.save(output, format="TIFF", compression="group4")
                candidates.append(output.getvalue())
            elif has_alpha:
                image.save(output, format="PNG", optimize=True)
                candidates.append(output.getvalue())
            else:
                # PNG often beats JPEG for diagrams and document scans. Keep
                # whichever encoding actually reduces the embedded stream.
                if image.mode not in {"RGB", "L", "P"}:
                    image = image.convert("RGB")
                image.save(output, format="PNG", optimize=True)
                candidates.append(output.getvalue())
                output = io.BytesIO()
                if image.mode not in {"RGB", "L"}:
                    image = image.convert("RGB")
                image.save(
                    output,
                    format="JPEG",
                    quality=jpeg_quality,
                    optimize=True,
                    progressive=True,
                )
                candidates.append(output.getvalue())

            candidate = min(candidates, key=len)
            source_size = original_size if original_size is not None else len(image_bytes)
            if len(candidate) >= source_size:
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
    candidate_path = output_path.with_suffix(".candidate.pdf")
    save_options = dict(
        garbage=4,
        deflate=True,
        deflate_images=True,
        deflate_fonts=True,
        use_objstms=1,
    )

    try:
        with fitz.open(input_path) as doc:
            if doc.needs_pass:
                raise ValueError(
                    "Password-protected PDFs are not supported for compression."
                )

            if doc.page_count < 1:
                raise ValueError("The PDF does not contain any pages.")

            page_count = doc.page_count
            # Editable forms may need characters that have not been entered yet.
            if not doc.is_form_pdf:
                doc.subset_fonts()
            doc.save(working_path, **save_options)

        # Keep the lossless result as a candidate: image replacement or content
        # stream cleanup can make some PDFs larger rather than smaller.
        with fitz.open(working_path) as doc:
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
                    **profile,
                    source_filter=source_filter,
                    original_size=len(doc.xref_stream_raw(xref)),
                )
                if replacement:
                    page = doc.load_page(page_number)
                    page.replace_image(xref, stream=replacement)

            doc.save(candidate_path, clean=True, **save_options)

        best_path = min(
            (path for path in (working_path, candidate_path) if path.exists()),
            key=lambda path: path.stat().st_size,
        )
        if best_path.stat().st_size >= input_path.stat().st_size:
            suggestion = (
                "Try a stronger compression level."
                if quality != "strong"
                else "The file is already optimized for these settings."
            )
            raise ValueError(
                f"This PDF could not be made smaller with {quality} compression "
                f"while preserving its content. {suggestion} Your original file is unchanged."
            )

        # Reopen the artifact so corrupt output is never marked successful.
        with fitz.open(best_path) as result:
            if result.page_count != page_count:
                raise ValueError("Compression produced an invalid PDF.")

        best_path.replace(output_path)
        return output_path
    finally:
        working_path.unlink(missing_ok=True)
        candidate_path.unlink(missing_ok=True)


def _deskew_scan(image: Image.Image, max_angle: float = 5.0) -> Image.Image:
    """Correct small scan angles using horizontal text-line projection."""

    grayscale = ImageOps.grayscale(image)
    scale = min(1.0, 1000 / max(grayscale.size))
    if scale < 1:
        grayscale = grayscale.resize(
            (max(1, round(grayscale.width * scale)), max(1, round(grayscale.height * scale))),
            Image.Resampling.BILINEAR,
        )

    ink = grayscale.point(lambda value: 255 if value < 190 else 0)
    best_angle = 0.0
    best_score = -1
    steps = round(max_angle * 2)

    for step in range(-steps, steps + 1):
        angle = step / 2
        candidate = ink.rotate(
            angle,
            resample=Image.Resampling.BILINEAR,
            expand=False,
            fillcolor=0,
        )
        projection = candidate.resize((1, candidate.height), Image.Resampling.BOX)
        score = sum(value * value for value in projection.getdata())

        if score > best_score:
            best_score = score
            best_angle = angle

    if math.isclose(best_angle, 0.0, abs_tol=0.2):
        return image

    return image.rotate(
        best_angle,
        resample=Image.Resampling.BICUBIC,
        expand=False,
        fillcolor="white",
    )


def _whiten_scan_background(image: Image.Image) -> Image.Image:
    """Fade light paper colors to white while retaining foreground content."""

    rgb = image.convert("RGB")
    whitening_mask = ImageOps.grayscale(rgb).point(
        lambda luminance: round(max(0.0, min(1.0, (luminance - 150) / 80)) * 255)
    )
    return Image.composite(Image.new("RGB", rgb.size, "white"), rgb, whitening_mask)


def _darken_scan_text(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    text_mask = ImageOps.grayscale(rgb).point(
        lambda luminance: 255 if luminance < 145 else 0
    )
    return Image.composite(Image.new("RGB", rgb.size, "black"), rgb, text_mask)


def _enhance_scan_font_weight(image: Image.Image) -> Image.Image:
    """Expand dark strokes by one pixel without turning the page monochrome."""

    rgb = image.convert("RGB")
    ink = ImageOps.invert(ImageOps.grayscale(rgb)).point(
        lambda value: 255 if value > 80 else 0
    )
    expanded_ink = ink.filter(ImageFilter.MaxFilter(3))
    new_ink = ImageChops.subtract(expanded_ink, ink)
    return Image.composite(Image.new("RGB", rgb.size, "black"), rgb, new_ink)


def _insert_searchable_text(page: fitz.Page, image: Image.Image) -> None:
    """Add invisible OCR glyphs so optimized scans remain searchable/selectable."""

    data = pytesseract.image_to_data(
        image,
        lang="eng",
        config="--psm 3",
        output_type=Output.DICT,
    )
    scale_x = page.rect.width / image.width
    scale_y = page.rect.height / image.height

    for index, raw_text in enumerate(data.get("text", [])):
        text = "".join(character for character in raw_text.strip() if ord(character) < 256)
        if not text:
            continue

        confidence = float(data["conf"][index])
        if confidence < 20:
            continue

        left = data["left"][index]
        top = data["top"][index]
        height = data["height"][index]
        page.insert_text(
            (left * scale_x, (top + height) * scale_y),
            text,
            fontsize=max(4, height * scale_y * 0.8),
            fontname="helv",
            render_mode=3,
            overlay=True,
        )


def optimize_pdf(
    input_path: Path,
    output_path: Path,
    options: Set[str],
    *,
    dpi: int = 200,
) -> Path:
    """Apply combinable scan-cleanup operations and create a new PDF."""

    _validate_pdf_path(input_path)
    invalid_options = options - OPTIMIZATION_OPTION_NAMES
    if invalid_options:
        raise ValueError(f"Unsupported optimization option: {sorted(invalid_options)[0]}.")
    if not options:
        raise ValueError("Select at least one optimization option.")
    if dpi < 150 or dpi > 300:
        raise ValueError("Optimization DPI must be between 150 and 300.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = fitz.open()

    try:
        with fitz.open(input_path) as source:
            if source.needs_pass:
                raise ValueError("Password-protected PDFs are not supported for optimization.")
            if source.page_count < 1:
                raise ValueError("The PDF does not contain any pages.")

            zoom = dpi / 72
            for source_page in source:
                pixmap = source_page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)

                if "deskew" in options:
                    image = _deskew_scan(image)
                if "whiten_background" in options:
                    image = _whiten_scan_background(image)
                if "darken_text" in options:
                    image = _darken_scan_text(image)
                if "enhance_font_weight" in options:
                    image = _enhance_scan_font_weight(image)
                if "invert_colors" in options:
                    image = ImageOps.invert(image.convert("RGB"))

                stream = io.BytesIO()
                image.save(stream, format="JPEG", quality=88, optimize=True, progressive=True)

                page = result.new_page(
                    width=source_page.rect.width,
                    height=source_page.rect.height,
                )
                page.insert_image(page.rect, stream=stream.getvalue())

                if "vectorize_text" in options:
                    _insert_searchable_text(page, image)

        result.save(output_path, garbage=4, deflate=True, use_objstms=1)
    finally:
        result.close()

    with fitz.open(output_path) as optimized:
        if optimized.page_count < 1:
            raise ValueError("Optimization produced an invalid PDF.")

    return output_path


def _render_comparison_page(page: fitz.Page, dpi: int) -> Image.Image:
    zoom = dpi / 72
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def _fit_on_canvas(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGB", size, "white")
    copy = image.copy()
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    left = (size[0] - copy.width) // 2
    top = (size[1] - copy.height) // 2
    canvas.paste(copy, (left, top))
    return canvas


def _comparison_report_image(
    reference: Image.Image,
    revised: Image.Image,
    page_number: int,
    status: str,
) -> tuple[Image.Image, float]:
    content_width = 760
    content_height = max(1, round(content_width * max(
        reference.height / max(reference.width, 1),
        revised.height / max(revised.width, 1),
    )))
    content_height = min(content_height, 1080)
    normalized_reference = _fit_on_canvas(reference, (content_width, content_height))
    normalized_revised = _fit_on_canvas(revised, (content_width, content_height))

    difference = ImageChops.difference(normalized_reference, normalized_revised)
    mask = ImageOps.grayscale(difference).point(lambda value: 255 if value > 24 else 0)
    mask = mask.filter(ImageFilter.MaxFilter(5))
    changed_pixels = sum(1 for value in mask.getdata() if value)
    change_percent = round(changed_pixels / (content_width * content_height) * 100, 2)
    if changed_pixels and change_percent == 0:
        change_percent = 0.01

    highlighted_revised = normalized_revised.copy()
    highlight = Image.new("RGB", highlighted_revised.size, (239, 68, 68))
    highlighted_revised = Image.blend(highlighted_revised, highlight, 0.42)
    normalized_revised.paste(highlighted_revised, mask=mask)

    margin = 42
    gutter = 32
    header_height = 105
    footer_height = 58
    report = Image.new(
        "RGB",
        (content_width * 2 + gutter + margin * 2, content_height + header_height + footer_height),
        "white",
    )
    draw = ImageDraw.Draw(report)
    draw.text((margin, 24), f"PDF comparison - page {page_number}", fill=(15, 23, 42))
    draw.text((margin, 56), "Original", fill=(71, 85, 105))
    draw.text((margin + content_width + gutter, 56), "New (changes highlighted)", fill=(71, 85, 105))

    top = header_height
    report.paste(normalized_reference, (margin, top))
    report.paste(normalized_revised, (margin + content_width + gutter, top))
    draw.rectangle((margin - 1, top - 1, margin + content_width, top + content_height), outline=(203, 213, 225))
    draw.rectangle(
        (
            margin + content_width + gutter - 1,
            top - 1,
            margin + content_width * 2 + gutter,
            top + content_height,
        ),
        outline=(203, 213, 225),
    )
    footer = f"{status}"
    if status == "Changed":
        footer += f" - {change_percent}% of the rendered page differs"
    draw.text((margin, top + content_height + 22), footer, fill=(190, 24, 93) if status != "Unchanged" else (22, 101, 52))
    return report, change_percent


def compare_pdfs(
    reference_path: Path,
    revised_path: Path,
    output_path: Path,
    *,
    dpi: int = 120,
) -> PdfComparisonResult:
    """Create a side-by-side visual comparison PDF with changed areas highlighted."""

    _validate_pdf_path(reference_path)
    _validate_pdf_path(revised_path)
    if dpi < 72 or dpi > 200:
        raise ValueError("Comparison DPI must be between 72 and 200.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = fitz.open()
    summary = {
        "pages_compared": 0,
        "changed_pages": 0,
        "unchanged_pages": 0,
        "added_pages": 0,
        "removed_pages": 0,
    }

    try:
        with fitz.open(reference_path) as reference_doc, fitz.open(revised_path) as revised_doc:
            if reference_doc.needs_pass or revised_doc.needs_pass:
                raise ValueError("Password-protected PDFs are not supported for comparison.")
            if reference_doc.page_count < 1 or revised_doc.page_count < 1:
                raise ValueError("Both PDFs must contain at least one page.")

            total_pages = max(reference_doc.page_count, revised_doc.page_count)
            summary["pages_compared"] = total_pages

            for page_index in range(total_pages):
                reference_image = (
                    _render_comparison_page(reference_doc[page_index], dpi)
                    if page_index < reference_doc.page_count
                    else None
                )
                revised_image = (
                    _render_comparison_page(revised_doc[page_index], dpi)
                    if page_index < revised_doc.page_count
                    else None
                )

                if reference_image is None:
                    reference_image = Image.new("RGB", revised_image.size, "white")
                    status = "Added page"
                    summary["added_pages"] += 1
                elif revised_image is None:
                    revised_image = Image.new("RGB", reference_image.size, "white")
                    status = "Removed page"
                    summary["removed_pages"] += 1
                else:
                    status = "Changed"

                report_image, change_percent = _comparison_report_image(
                    reference_image,
                    revised_image,
                    page_index + 1,
                    status,
                )
                if status == "Changed":
                    if change_percent == 0:
                        status = "Unchanged"
                        summary["unchanged_pages"] += 1
                        report_image, _ = _comparison_report_image(
                            reference_image,
                            revised_image,
                            page_index + 1,
                            status,
                        )
                    else:
                        summary["changed_pages"] += 1

                stream = io.BytesIO()
                report_image.save(stream, format="JPEG", quality=88, optimize=True)
                pdf_page = report.new_page(
                    width=report_image.width * 0.5,
                    height=report_image.height * 0.5,
                )
                pdf_page.insert_image(pdf_page.rect, stream=stream.getvalue())

        report.set_metadata({
            "title": "PDF comparison report",
            "subject": "Side-by-side visual differences between two PDF files",
            "creator": "UpgradePDF",
        })
        report.save(output_path, garbage=4, deflate=True, use_objstms=1)
        (output_path.parent / "comparison.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )
    finally:
        report.close()

    with fitz.open(output_path) as generated:
        if generated.page_count != summary["pages_compared"]:
            raise ValueError("Comparison produced an invalid report.")

    return PdfComparisonResult(output_path=output_path, summary=summary)


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
