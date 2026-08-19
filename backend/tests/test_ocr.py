import tempfile
import unittest
from pathlib import Path

import fitz
from fastapi import HTTPException
from PIL import Image

from app.modules.ocr.service import (
    MAX_TIMEOUT_SECONDS,
    clamp_timeout,
    ensure_pdf_input,
    extract_text_from_searchable_pdf,
    parse_language_codes,
)
from app.modules.ocr.storage import get_job_dir, public_status_payload, safe_filename
from app.modules.ocr.tasks import process_ocr_job
from app.workers.celery_app import celery_app


class OcrServiceTests(unittest.TestCase):
    def test_language_parser_supports_mixed_languages_and_deduplicates(self):
        self.assertEqual(parse_language_codes("eng,hin+eng"), ["eng", "hin"])
        self.assertEqual(parse_language_codes(None), ["eng"])

    def test_language_parser_rejects_unsupported_languages(self):
        with self.assertRaisesRegex(ValueError, "Unsupported OCR language"):
            parse_language_codes("eng+unknown")

    def test_timeout_is_clamped_to_safe_bounds(self):
        self.assertEqual(clamp_timeout(1), 60)
        self.assertEqual(clamp_timeout(MAX_TIMEOUT_SECONDS + 100), MAX_TIMEOUT_SECONDS)

    def test_image_input_is_converted_to_a_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "scan.png"
            Image.new("RGB", (200, 100), "white").save(source)

            output = ensure_pdf_input(source, root / "work")

            with fitz.open(output) as document:
                self.assertEqual(document.page_count, 1)

    def test_searchable_pdf_text_export_includes_page_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_path = root / "searchable.pdf"
            with fitz.open() as document:
                page = document.new_page()
                page.insert_text((72, 72), "Searchable text")
                document.save(pdf_path)

            text_path = extract_text_from_searchable_pdf(pdf_path, root / "output" / "ocr.txt")
            exported = text_path.read_text(encoding="utf-8")
            self.assertIn("Page 1", exported)
            self.assertIn("Searchable text", exported)


class OcrContractTests(unittest.TestCase):
    def test_filename_and_job_id_validation_prevent_path_traversal(self):
        self.assertEqual(safe_filename("../../unsafe scan.pdf"), "unsafe_scan.pdf")
        with self.assertRaises(HTTPException) as raised:
            get_job_dir("../not-a-job")
        self.assertEqual(raised.exception.status_code, 400)

    def test_public_status_only_advertises_existing_output_references(self):
        payload = public_status_payload(
            {
                "job_id": "a" * 32,
                "status": "completed",
                "percent": 100,
                "message": "done",
                "output_pdf": "output/result.pdf",
                "output_text": None,
            }
        )
        self.assertTrue(payload["output_pdf_available"])
        self.assertFalse(payload["output_text_available"])
        self.assertEqual(payload["percent"], 100)

    def test_worker_registers_ocr_task_on_the_ocr_queue(self):
        task_name = "app.modules.ocr.tasks.process_ocr_job"
        self.assertIn(task_name, celery_app.tasks)
        self.assertEqual(celery_app.conf.task_routes[task_name]["queue"], "ocr")
        self.assertEqual(process_ocr_job.name, task_name)


if __name__ == "__main__":
    unittest.main()
