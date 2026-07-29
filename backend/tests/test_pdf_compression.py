import io
import tempfile
import unittest
from pathlib import Path

import fitz
from PIL import Image

from app.services.pdf_service import compress_pdf


class PdfCompressionTests(unittest.TestCase):
    def _create_image_heavy_pdf(self, path: Path) -> None:
        image = Image.effect_noise((2600, 1800), 80).convert("RGB")
        image_buffer = io.BytesIO()
        image.save(image_buffer, format="PNG")

        with fitz.open() as document:
            page = document.new_page(width=612, height=792)
            page.insert_text((50, 50), "Compression keeps this text searchable.")
            page.insert_image(
                fitz.Rect(40, 90, 572, 680),
                stream=image_buffer.getvalue(),
            )
            document.save(path)

    def test_strong_compression_reduces_size_and_preserves_content(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.pdf"
            output_path = Path(directory) / "compressed.pdf"
            self._create_image_heavy_pdf(input_path)

            compress_pdf(input_path, output_path, "strong")

            self.assertLess(output_path.stat().st_size, input_path.stat().st_size)
            with fitz.open(output_path) as result:
                self.assertEqual(result.page_count, 1)
                self.assertIn("Compression keeps", result[0].get_text())

    def test_invalid_quality_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.pdf"
            output_path = Path(directory) / "compressed.pdf"
            self._create_image_heavy_pdf(input_path)

            with self.assertRaisesRegex(ValueError, "Quality must be"):
                compress_pdf(input_path, output_path, "extreme")


if __name__ == "__main__":
    unittest.main()
