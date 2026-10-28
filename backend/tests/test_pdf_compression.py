import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_all_levels_reduce_images_below_the_old_resize_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.pdf"
            self._create_image_heavy_pdf(source)
            previous_size = source.stat().st_size

            for level in ("light", "balanced", "strong"):
                with self.subTest(level=level):
                    output = compress_pdf(source, root / f"{level}.pdf", level)
                    self.assertLess(output.stat().st_size, previous_size)
                    previous_size = output.stat().st_size
                    with fitz.open(output) as result:
                        self.assertEqual(result.page_count, 1)
                        self.assertIn("Compression keeps", result[0].get_text())

    def test_all_levels_subset_embedded_fonts_without_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.pdf"
            with fitz.open() as document:
                page = document.new_page()
                page.insert_font(fontname="embedded", fontbuffer=fitz.Font("cjk").buffer)
                page.insert_text((50, 50), "Searchable ABC", fontname="embedded")
                document.save(source, deflate=True, garbage=4, use_objstms=1)
            with fitz.open(source) as document:
                expected_text = document[0].get_text()

            for level in ("light", "balanced", "strong"):
                with self.subTest(level=level):
                    output = compress_pdf(source, root / f"{level}.pdf", level)
                    self.assertLess(output.stat().st_size, source.stat().st_size)
                    with fitz.open(output) as result:
                        self.assertEqual(result[0].get_text(), expected_text)

    def test_minimal_pdf_is_not_reported_as_a_successful_compression(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "minimal.pdf"
            with fitz.open() as document:
                document.new_page()
                document.save(source, garbage=4, deflate=True, use_objstms=1)
            original = source.read_bytes()

            for level in ("light", "balanced", "strong"):
                with self.subTest(level=level):
                    output = root / f"{level}.pdf"
                    with self.assertRaisesRegex(ValueError, "could not be made smaller"):
                        compress_pdf(source, output, level)
                    self.assertFalse(output.exists())
                    self.assertFalse(output.with_suffix(".working.pdf").exists())
                    self.assertFalse(output.with_suffix(".candidate.pdf").exists())
                    self.assertEqual(source.read_bytes(), original)

    def test_links_forms_and_masked_images_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.pdf"
            self._create_image_heavy_pdf(source)
            enriched = root / "with-form.pdf"
            with fitz.open(source) as document:
                page = document[0]
                page.insert_link({
                    "kind": fitz.LINK_URI,
                    "from": fitz.Rect(40, 30, 300, 60),
                    "uri": "https://example.com",
                })
                widget = fitz.Widget()
                widget.field_name = "reference"
                widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
                widget.field_value = "ABC 123"
                widget.rect = fitz.Rect(40, 700, 250, 730)
                page.add_widget(widget)
                rgba = Image.new("RGBA", (320, 320), (0, 80, 220, 128))
                stream = io.BytesIO()
                rgba.save(stream, format="PNG")
                page.insert_image(fitz.Rect(400, 690, 460, 750), stream=stream.getvalue())
                document.save(enriched, deflate=True)

            for level in ("light", "balanced", "strong"):
                with self.subTest(level=level):
                    output = compress_pdf(enriched, root / f"{level}.pdf", level)
                    with fitz.open(output) as result:
                        self.assertIn("Compression keeps", result[0].get_text())
                        self.assertEqual(result[0].get_links()[0]["uri"], "https://example.com")
                        fields = list(result[0].widgets())
                        self.assertEqual(fields[0].field_name, "reference")
                        self.assertEqual(fields[0].field_value, "ABC 123")
                        masked = [im for im in result[0].get_images() if im[1]]
                        self.assertEqual(len(masked), 1)
                        self.assertEqual(masked[0][2:4], (320, 320))

    def test_no_reduction_marks_the_job_failed_instead_of_completed(self):
        from app.workers.tasks import compress_pdf_task

        with (
            patch("app.workers.tasks.mark_job_processing"),
            patch("app.workers.tasks.mark_job_completed") as completed,
            patch("app.workers.tasks.mark_job_failed") as failed,
            patch("app.workers.tasks.compress_pdf", side_effect=ValueError("could not be made smaller")),
        ):
            with self.assertRaisesRegex(ValueError, "could not be made smaller"):
                compress_pdf_task.run("test-job", "balanced")
            completed.assert_not_called()
            failed.assert_called_once_with(job_id="test-job", error_message="could not be made smaller")

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
