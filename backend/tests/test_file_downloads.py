import unittest
from types import SimpleNamespace

from app.api.routes.files import _download_filename
from app.models.job import JobOperation


class FileDownloadTests(unittest.TestCase):
    def test_compressed_pdf_keeps_uploaded_filename(self):
        job = SimpleNamespace(
            operation=JobOperation.COMPRESS,
            input_filename="Quarterly report.pdf",
        )

        self.assertEqual(
            _download_filename(job, "compressed.pdf"),
            "Quarterly report.pdf",
        )

    def test_compressed_pdf_without_input_filename_uses_stored_filename(self):
        job = SimpleNamespace(
            operation=JobOperation.COMPRESS,
            input_filename=None,
        )

        self.assertEqual(
            _download_filename(job, "compressed.pdf"),
            "compressed.pdf",
        )

    def test_other_operations_keep_their_generated_filename(self):
        job = SimpleNamespace(
            operation=JobOperation.SPLIT,
            input_filename="Quarterly report.pdf",
        )

        self.assertEqual(
            _download_filename(job, "split_pages.pdf"),
            "split_pages.pdf",
        )


if __name__ == "__main__":
    unittest.main()
