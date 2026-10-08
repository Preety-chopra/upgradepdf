import tempfile
import unittest
from pathlib import Path

import fitz

from app.services.pdf_service import (
    _parse_page_order,
    _parse_pages,
    delete_pages,
    extract_pages,
    merge_pdfs,
    reorder_pdf,
    rotate_pdf,
)


def create_pdf(path: Path, labels: list[str]) -> Path:
    with fitz.open() as document:
        for label in labels:
            page = document.new_page()
            page.insert_text((72, 72), label)
        document.save(path)
    return path


class PageSelectionTests(unittest.TestCase):
    def test_page_ranges_are_normalized_and_deduplicated(self):
        self.assertEqual(_parse_pages("3,1-2,2", 4), [0, 1, 2])
        self.assertEqual(_parse_pages("all", 3), [0, 1, 2])

    def test_invalid_page_ranges_are_rejected(self):
        invalid_values = ("", "0", "4", "3-1", "one")
        for value in invalid_values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                _parse_pages(value, 3)

    def test_page_order_requires_an_exact_permutation(self):
        self.assertEqual(_parse_page_order("3, 1, 2", 3), [2, 0, 1])

        for value in ("", "1,2", "1,2,2", "1,2,4", "one,2,3"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                _parse_page_order(value, 3)


class PdfToolTests(unittest.TestCase):
    def test_reorder_saves_pages_in_the_requested_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = create_pdf(root / "source.pdf", ["One", "Two", "Three"])
            output = reorder_pdf(source, root / "reordered.pdf", "3,1,2")

            with fitz.open(output) as document:
                self.assertEqual(document.page_count, 3)
                self.assertIn("Three", document[0].get_text())
                self.assertIn("One", document[1].get_text())
                self.assertIn("Two", document[2].get_text())

    def test_merge_combines_documents_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = create_pdf(root / "first.pdf", ["First page"])
            second = create_pdf(root / "second.pdf", ["Second page", "Third page"])
            output = merge_pdfs([first, second], root / "merged.pdf")

            with fitz.open(output) as document:
                self.assertEqual(document.page_count, 3)
                self.assertIn("First page", document[0].get_text())
                self.assertIn("Second page", document[1].get_text())
                self.assertIn("Third page", document[2].get_text())

    def test_merge_requires_at_least_two_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            only = create_pdf(root / "only.pdf", ["Only page"])
            with self.assertRaisesRegex(ValueError, "At least two"):
                merge_pdfs([only], root / "merged.pdf")

    def test_split_extracts_requested_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = create_pdf(root / "source.pdf", ["One", "Two", "Three"])
            output = extract_pages(source, root / "split.pdf", "1,3")

            with fitz.open(output) as document:
                self.assertEqual(document.page_count, 2)
                self.assertIn("One", document[0].get_text())
                self.assertIn("Three", document[1].get_text())

    def test_rotate_changes_only_selected_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = create_pdf(root / "source.pdf", ["One", "Two"])
            output = rotate_pdf(source, root / "rotated.pdf", "2", 90)

            with fitz.open(output) as document:
                self.assertEqual(document[0].rotation, 0)
                self.assertEqual(document[1].rotation, 90)

    def test_rotate_rejects_unsupported_angles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = create_pdf(root / "source.pdf", ["One"])
            with self.assertRaisesRegex(ValueError, "Angle must be"):
                rotate_pdf(source, root / "rotated.pdf", "all", 45)

    def test_delete_pages_keeps_unselected_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = create_pdf(root / "source.pdf", ["One", "Two", "Three"])
            output = delete_pages(source, root / "remaining.pdf", "2")

            with fitz.open(output) as document:
                self.assertEqual(document.page_count, 2)
                self.assertIn("One", document[0].get_text())
                self.assertIn("Three", document[1].get_text())

    def test_delete_pages_never_creates_an_empty_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = create_pdf(root / "source.pdf", ["One"])
            with self.assertRaisesRegex(ValueError, "Cannot delete all pages"):
                delete_pages(source, root / "empty.pdf", "all")


if __name__ == "__main__":
    unittest.main()
