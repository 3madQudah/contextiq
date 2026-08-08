"""
Tests for PDF scanned/image-based detection (loaders/document_loader.py).

OCR is deliberately not implemented (see load_pdf_with_scan_detection's
docstring: it needs the system `tesseract` binary, which isn't installed in
this environment, plus the `pytesseract`/`PyMuPDF` pip packages, also not
installed) -- so what's tested here is the detection + clear-error path, not
an OCR fallback. is_likely_scanned_pdf() is pure and portable (just takes
plain strings), so it's tested directly; the "scanned PDF" fixture uses
pypdf.PdfWriter().add_blank_page() -- a real, minimal, dependency-free PDF
with no text layer at all -- rather than any external tool.
"""

import os

import pytest
from pypdf import PdfWriter

from loaders.document_loader import (
    ScannedPDFError,
    is_likely_scanned_pdf,
    load_document,
    load_pdf_with_scan_detection,
)

FIXTURES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "eval",
    "fixtures",
)


def _write_blank_pdf(path: str, num_pages: int) -> None:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=612, height=792)
    with open(path, "wb") as f:
        writer.write(f)


def test_is_likely_scanned_pdf_all_empty_pages():
    assert is_likely_scanned_pdf(["", "", ""]) is True


def test_is_likely_scanned_pdf_normal_text():
    assert is_likely_scanned_pdf(["This is a real page of extracted text, plenty of characters."] * 3) is False


def test_is_likely_scanned_pdf_mostly_empty_with_one_real_page():
    # A cover/divider page or two being blank shouldn't flag an otherwise
    # normal document -- only when *most* pages are near-empty.
    assert is_likely_scanned_pdf(["", "A real page with plenty of extracted text content here.", ""]) is False


def test_is_likely_scanned_pdf_empty_input():
    assert is_likely_scanned_pdf([]) is False


def test_scanned_pdf_raises_clear_actionable_error(tmp_path):
    path = tmp_path / "scanned.pdf"
    _write_blank_pdf(str(path), num_pages=2)

    with pytest.raises(ScannedPDFError) as exc_info:
        load_pdf_with_scan_detection(str(path))

    message = str(exc_info.value)
    assert "scanned" in message.lower()
    # The specific missing pieces + how to install them, per the task this
    # module was built for -- not just a generic "OCR not supported".
    assert "tesseract" in message.lower()
    assert "pytesseract" in message.lower()
    assert "pymupdf" in message.lower()
    assert "brew install tesseract" in message  # a concrete, copy-pasteable step


def test_scanned_pdf_routed_through_load_document(tmp_path):
    """load_document() (the actual ingestion entry point) raises the same
    error for a .pdf extension, not just the dedicated loader function."""
    path = tmp_path / "scanned.pdf"
    _write_blank_pdf(str(path), num_pages=1)

    with pytest.raises(ScannedPDFError):
        load_document(str(path))


def test_normal_text_pdf_loads_without_error():
    """Regression check: a real PDF with an actual text layer must NOT be
    misflagged as scanned. Reuses an existing fixture PDF from eval/fixtures
    (built from real extractable text in an earlier task) rather than
    depending on any PDF-generation tool being available here."""
    path = os.path.join(FIXTURES_DIR, "board_meeting_minutes.pdf")
    docs = load_document(path)

    assert len(docs) >= 1
    assert any(doc.page_content.strip() for doc in docs)
