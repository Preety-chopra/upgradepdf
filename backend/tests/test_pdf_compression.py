import io
import tempfile
import unittest
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

from app.services.pdf_service import _encode_compressed_image, compress_pdf


class PdfCompressionTests(unittest.TestCase):
    def _create_image_heavy_pdf(self, path: Path) -> None:
        image = Image.effect_noise((1400, 1000), 80).convert("RGB")
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

    def test_ccitt_scan_uses_bilevel_downsampling(self):
        image = Image.new("1", (2400, 3200), color=1)
        drawing = ImageDraw.Draw(image)
        for y in range(100, 3100, 80):
            drawing.rectangle((100, y, 2300, y + 20), fill=0)

        source = io.BytesIO()
        image.save(source, format="TIFF", compression="group4")

        compressed = _encode_compressed_image(
            source.getvalue(),
            max_dimension=1200,
            jpeg_quality=55,
            source_filter="CCITTFaxDecode",
        )

        self.assertIsNotNone(compressed)
        with Image.open(io.BytesIO(compressed)) as result:
            self.assertEqual(result.mode, "1")
            self.assertLessEqual(max(result.size), 1200)


if __name__ == "__main__":
    unittest.main()
