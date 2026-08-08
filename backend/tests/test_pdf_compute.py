"""
Tests for the PDF full-document query path (chain/pdf_compute.py and
chain/pdf_query_classifier.py).

Both the LLM call (chain.pdf_compute._llm) and pypdf's PdfReader
(chain.pdf_compute.PdfReader) are monkeypatched to lightweight fakes -- the
fake reader takes plain page-text strings and an optional outline, entirely
sidestepping the need to generate real PDF bytes with a real text layer just
to test extraction/prompt-building logic. Portable (no external PDF-
generation tool required) and fast. loaders/document_loader.py's actual
PyPDFLoader-based extraction is covered separately in
tests/test_document_loader_pdf.py.
"""

import pytest

from chain import pdf_compute
from chain.pdf_query_classifier import is_full_document_question


class _FakeResponse:
    def __init__(self, content):
        self.content = content


class _FakeLLM:
    def __init__(self, prompts):
        self._prompts = prompts

    def invoke(self, prompt):
        self._prompts.append(prompt)
        return _FakeResponse("STUBBED_ANSWER")


class _FakePage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class _FakeOutlineItem:
    """Mimics pypdf's Destination enough for _extract_outline_titles: a
    .title attribute, nothing else needed."""

    def __init__(self, title):
        self.title = title


class _FakeReader:
    def __init__(self, page_texts, outline=None):
        self.pages = [_FakePage(t) for t in page_texts]
        self.outline = outline or []


PAGE_1 = "Policy Overview\n\nThis policy governs remote work arrangements company-wide."
PAGE_2 = (
    "Eligibility\n\nAll full-time employees are eligible after 90 days of tenure. "
    "The policy took effect on 2024-01-15."
)
PAGE_3 = (
    "Approval Process\n\nManagers must approve requests within 5 business days, "
    "a deadline last revised on 2025-03-01."
)


@pytest.fixture
def pdf_user(tmp_path, monkeypatch):
    """Point pdf_compute at a temp raw-data dir, stub the LLM call, and fake
    out PdfReader so tests control extracted page text/outline directly."""
    monkeypatch.setattr(pdf_compute, "RAW_DATA_DIR", str(tmp_path))

    prompts = []
    monkeypatch.setattr(pdf_compute, "_llm", lambda: _FakeLLM(prompts))

    fake_readers = {}
    monkeypatch.setattr(pdf_compute, "PdfReader", lambda path: fake_readers[path])

    def _write(user_id: int, file_name: str, page_texts=(PAGE_1, PAGE_2, PAGE_3), outline=None):
        user_dir = tmp_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        path = user_dir / file_name
        path.write_bytes(b"%PDF-fake-content-real-parsing-is-mocked")
        fake_readers[str(path)] = _FakeReader(list(page_texts), outline)

    return prompts, _write


def test_full_document_summary_uses_complete_text(pdf_user):
    prompts, write = pdf_user
    write(1, "policy.pdf")

    result = pdf_compute.answer_full_document_question(
        user_id=1, question="Please summarize the entire document", file_name="policy.pdf"
    )

    assert result is not None
    assert result["sources"] == ["policy.pdf"]
    assert result["answer"] == "STUBBED_ANSWER"
    (prompt,) = prompts
    assert "90 days of tenure" in prompt
    assert "last revised on 2025-03-01" in prompt  # content from the final page


def test_exhaustive_date_extraction_uses_complete_text(pdf_user):
    prompts, write = pdf_user
    write(1, "policy.pdf")

    result = pdf_compute.answer_full_document_question(
        user_id=1, question="List every date mentioned in the document", file_name="policy.pdf"
    )

    assert result is not None
    (prompt,) = prompts
    assert "exhaustive" in prompt.lower()
    assert "date" in prompt.lower()
    assert "2024-01-15" in prompt
    assert "2025-03-01" in prompt


def test_fallback_when_question_is_not_full_document(pdf_user):
    _, write = pdf_user
    write(1, "policy.pdf")
    question = "What is the approval process for remote work?"

    assert is_full_document_question(question) is False

    result = pdf_compute.answer_full_document_question(user_id=1, question=question, file_name="policy.pdf")
    assert result is None


def test_page_count_is_exact_and_not_asked_of_llm(pdf_user):
    """Unlike DOCX, PDF page count is a reliable structural fact -- see
    chain/pdf_compute.py's module docstring -- so this asserts it's reported
    plainly (no caveat) and matches the real number of pages given."""
    prompts, write = pdf_user
    write(1, "policy.pdf", page_texts=(PAGE_1, PAGE_2, PAGE_3))

    result = pdf_compute.answer_full_document_question(
        user_id=1, question="How many pages does this document have?", file_name="policy.pdf"
    )

    assert result is not None
    (prompt,) = prompts
    assert "Page count: 3" in prompt
    assert "not reliably available" not in prompt  # that caveat is DOCX-specific, must not leak here


def test_heading_list_uses_outline_when_present(pdf_user):
    prompts, write = pdf_user
    write(
        1,
        "policy.pdf",
        outline=[_FakeOutlineItem("Policy Overview"), _FakeOutlineItem("Eligibility")],
    )

    result = pdf_compute.answer_full_document_question(
        user_id=1, question="What is the table of contents for this document?", file_name="policy.pdf"
    )

    assert result is not None
    (prompt,) = prompts
    assert "Policy Overview" in prompt
    assert "Eligibility" in prompt


def test_heading_list_reports_honestly_when_no_outline(pdf_user):
    """Most real-world PDFs (scans, plain exports) have no embedded outline
    at all -- this must be stated plainly, not silently reported as an empty
    (and misleadingly "complete") list."""
    prompts, write = pdf_user
    write(1, "policy.pdf", outline=None)

    result = pdf_compute.answer_full_document_question(
        user_id=1, question="What is the table of contents for this document?", file_name="policy.pdf"
    )

    assert result is not None
    (prompt,) = prompts
    assert "no embedded outline" in prompt.lower()


def test_too_large_document_declines_instead_of_truncating(pdf_user, monkeypatch):
    prompts, write = pdf_user
    write(1, "policy.pdf")
    monkeypatch.setattr(pdf_compute, "MAX_DOCUMENT_CHARS", 10)

    result = pdf_compute.answer_full_document_question(
        user_id=1, question="Summarize the whole document", file_name="policy.pdf"
    )

    assert result is not None
    assert "too long" in result["answer"]
    assert prompts == []


def test_scanned_pdf_short_circuits_with_honest_answer(pdf_user):
    """A scanned PDF that somehow made it past upload-time detection (e.g.
    ingested before this check existed) must still be handled honestly here,
    not summarized as if its near-empty extracted text were real content."""
    prompts, write = pdf_user
    write(1, "scanned.pdf", page_texts=("", "", ""))

    result = pdf_compute.answer_full_document_question(
        user_id=1, question="Summarize the whole document", file_name="scanned.pdf"
    )

    assert result is not None
    assert "scanned" in result["answer"].lower()
    assert prompts == []  # never asked the LLM to summarize empty text
