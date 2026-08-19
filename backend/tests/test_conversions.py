import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import fitz
import pandas as pd
from docx import Document
from fastapi import HTTPException
from PIL import Image
from starlette.datastructures import UploadFile

from app.modules.conversions.security import require_extension, safe_filename, save_upload_file
from app.modules.conversions.service import (
    _looks_like_scanned_pdf,
    images_to_pdf,
    pdf_to_csv_or_zip,
    pdf_to_jpg_zip,
    pdf_to_text_docx,
    pdf_to_xlsx,
)


def create_text_pdf(path: Path, labels: list[str]) -> Path:
    with fitz.open() as document:
        for label in labels:
            page = document.new_page()
            page.insert_text((72, 72), label)
        document.save(path)
    return path


class ConversionServiceTests(unittest.TestCase):
    def test_images_to_pdf_combines_jpg_and_transparent_png(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jpg = root / "first.jpg"
            png = root / "second.png"
            Image.new("RGB", (120, 80), "red").save(jpg)
            Image.new("RGBA", (80, 120), (0, 0, 255, 100)).save(png)

            output = images_to_pdf([jpg, png], root / "output" / "images.pdf")

            self.assertTrue(output.exists())
            with fitz.open(output) as document:
                self.assertEqual(document.page_count, 2)

    def test_images_to_pdf_requires_an_image(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(HTTPException) as raised:
                images_to_pdf([], Path(directory) / "images.pdf")
            self.assertEqual(raised.exception.status_code, 400)

    def test_pdf_to_jpg_creates_one_valid_image_per_page(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = create_text_pdf(root / "source.pdf", ["One", "Two"])
            archive = pdf_to_jpg_zip(source, root / "output", dpi=72, quality=80)

            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                self.assertEqual(len(names), 2)
                self.assertTrue(all(name.endswith(".jpg") for name in names))
                with Image.open(io.BytesIO(bundle.read(names[0]))) as image:
                    self.assertEqual(image.format, "JPEG")

    def test_pdf_to_jpg_validates_render_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            source = create_text_pdf(Path(directory) / "source.pdf", ["One"])
            for kwargs in ({"dpi": 50}, {"quality": 40}):
                with self.subTest(kwargs=kwargs), self.assertRaises(HTTPException):
                    pdf_to_jpg_zip(source, Path(directory) / "output", **kwargs)

    def test_pdf_to_text_docx_preserves_page_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = create_text_pdf(root / "source.pdf", ["Alpha", "Beta"])
            output = pdf_to_text_docx(source, root / "converted.docx")

            text = "\n".join(paragraph.text for paragraph in Document(output).paragraphs)
            self.assertIn("Alpha", text)
            self.assertIn("Beta", text)

    def test_scanned_pdf_detection_distinguishes_text_layers(self):
        scanned = {"page_count": 4, "text_pages": 0, "text_chars": 0, "text_page_ratio": 0.0}
        digital = {"page_count": 4, "text_pages": 4, "text_chars": 2000, "text_page_ratio": 1.0}
        self.assertTrue(_looks_like_scanned_pdf(scanned))
        self.assertFalse(_looks_like_scanned_pdf(digital))

    def test_table_exports_create_xlsx_and_csv(self):
        tables = [("page_1_table_1", pd.DataFrame([["Name", "Value"], ["A", "1"]]))]
        with tempfile.TemporaryDirectory() as directory, patch(
            "app.modules.conversions.service.extract_pdf_tables", return_value=tables
        ):
            root = Path(directory)
            xlsx = pdf_to_xlsx(root / "source.pdf", root / "tables.xlsx")
            csv_path = pdf_to_csv_or_zip(root / "source.pdf", root / "csv")

            self.assertTrue(xlsx.exists())
            self.assertTrue(csv_path.exists())
            self.assertEqual(csv_path.suffix, ".csv")


class ConversionUploadTests(unittest.IsolatedAsyncioTestCase):
    def test_safe_filename_removes_paths_and_unsafe_characters(self):
        self.assertEqual(safe_filename("../unsafe name?.png"), "unsafe_name_.png")

    def test_extension_validation_is_case_insensitive(self):
        self.assertEqual(require_extension("photo.JPEG", {".jpg", ".jpeg"}), ".jpeg")
        with self.assertRaises(HTTPException):
            require_extension("payload.exe", {".jpg"})

    async def test_upload_is_saved_with_validated_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            upload = UploadFile(io.BytesIO(b"image-data"), filename="my image.PNG")
            output = await save_upload_file(upload, Path(directory), {".png"})
            self.assertEqual(output.name, "my_image.PNG")
            self.assertEqual(output.read_bytes(), b"image-data")

    async def test_empty_upload_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            upload = UploadFile(io.BytesIO(b""), filename="empty.png")
            with self.assertRaises(HTTPException) as raised:
                await save_upload_file(upload, Path(directory), {".png"})
            self.assertEqual(raised.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
