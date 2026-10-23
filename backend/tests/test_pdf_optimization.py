import io
import tempfile
import unittest
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageStat

from app.services.pdf_service import optimize_pdf


class PdfOptimizationTests(unittest.TestCase):
    def _create_scan_pdf(self, path: Path) -> None:
        image = Image.new("RGB", (800, 1000), (238, 229, 190))
        drawing = ImageDraw.Draw(image)
        drawing.rectangle((90, 140, 700, 172), fill=(105, 100, 88))
        drawing.rectangle((90, 210, 620, 232), fill=(125, 118, 102))

        stream = io.BytesIO()
        image.save(stream, format="PNG")
        with fitz.open() as document:
            page = document.new_page(width=400, height=500)
            page.insert_image(page.rect, stream=stream.getvalue())
            document.save(path)

    def test_combined_cleanup_preserves_page_geometry_and_whitens_background(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "scan.pdf"
            output_path = Path(directory) / "optimized.pdf"
            self._create_scan_pdf(input_path)

            optimize_pdf(
                input_path,
                output_path,
                {"whiten_background", "darken_text", "enhance_font_weight"},
                dpi=150,
            )

            with fitz.open(output_path) as result:
                self.assertEqual(result.page_count, 1)
                self.assertAlmostEqual(result[0].rect.width, 400)
                self.assertAlmostEqual(result[0].rect.height, 500)
                pixmap = result[0].get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
                optimized = Image.frombytes(
                    "RGB", (pixmap.width, pixmap.height), pixmap.samples
                )

            background = optimized.crop((10, 10, 70, 70))
            self.assertGreater(ImageStat.Stat(background).mean[0], 245)

    def test_invert_colors_changes_white_page_to_dark(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "scan.pdf"
            output_path = Path(directory) / "optimized.pdf"
            self._create_scan_pdf(input_path)

            optimize_pdf(input_path, output_path, {"invert_colors"}, dpi=150)

            with fitz.open(output_path) as result:
                pixmap = result[0].get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
                optimized = Image.frombytes(
                    "RGB", (pixmap.width, pixmap.height), pixmap.samples
                )
            self.assertLess(ImageStat.Stat(optimized.crop((10, 10, 70, 70))).mean[0], 40)

    def test_requires_at_least_one_known_option(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "scan.pdf"
            output_path = Path(directory) / "optimized.pdf"
            self._create_scan_pdf(input_path)

            with self.assertRaisesRegex(ValueError, "at least one"):
                optimize_pdf(input_path, output_path, set())
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                optimize_pdf(input_path, output_path, {"sharpen_everything"})


if __name__ == "__main__":
    unittest.main()
