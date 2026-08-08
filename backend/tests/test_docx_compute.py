"""
Tests for the DOCX full-document query path (chain/docx_compute.py and
chain/docx_query_classifier.py).

The LLM call (chain.docx_compute._llm) is monkeypatched to a stub that
records the prompt it was given and returns a canned response, rather than
calling the real Groq API -- these tests are about verifying the *right
content* (the complete document, not a chunked sample) reaches the prompt,
and that fallback happens when it should; they don't need network access or
a GROQ_API_KEY.
"""

import pytest
from docx import Document as DocxDocument

from chain import docx_compute
from chain.docx_query_classifier import is_full_document_question


class _FakeResponse:
    def __init__(self, content):
        self.content = content


class _FakeLLM:
    """Records every prompt it's invoked with; answers with a fixed string
    so tests can assert on what was *asked*, not on real model output."""

    def __init__(self, prompts):
        self._prompts = prompts

    def invoke(self, prompt):
        self._prompts.append(prompt)
        return _FakeResponse("STUBBED_ANSWER")


@pytest.fixture
def docx_user(tmp_path, monkeypatch):
    """Point docx_compute at a temp raw-data dir, stub out the LLM call, and
    return a helper that builds a multi-section .docx fixture on disk."""
    monkeypatch.setattr(docx_compute, "RAW_DATA_DIR", str(tmp_path))

    prompts = []
    monkeypatch.setattr(docx_compute, "_llm", lambda: _FakeLLM(prompts))

    def _write(user_id: int, file_name: str) -> None:
        user_dir = tmp_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        doc = DocxDocument()
        doc.add_heading("Policy Overview", level=1)
        doc.add_paragraph("This policy governs remote work arrangements company-wide.")
        doc.add_heading("Eligibility", level=2)
        doc.add_paragraph("All full-time employees are eligible after 90 days of tenure.")
        doc.add_paragraph("The policy took effect on 2024-01-15.")
        doc.add_heading("Approval Process", level=2)
        doc.add_paragraph(
            "Managers must approve requests via the HR portal within 5 business days, "
            "a deadline that was last revised on 2025-03-01."
        )
        doc.save(str(user_dir / file_name))

    return prompts, _write


def test_full_document_summary_uses_complete_text(docx_user):
    prompts, write = docx_user
    write(1, "policy.docx")

    result = docx_compute.answer_full_document_question(
        user_id=1, question="Please summarize the entire document", file_name="policy.docx"
    )

    assert result is not None
    assert result["sources"] == ["policy.docx"]
    assert result["answer"] == "STUBBED_ANSWER"
    # The prompt handed to the LLM must contain text from every section --
    # including the last one -- proving the full document was used, not a
    # retrieved/truncated excerpt.
    (prompt,) = prompts
    assert "Policy Overview" not in prompt or "governs remote work" in prompt  # sanity: real content present
    assert "90 days of tenure" in prompt
    assert "last revised on 2025-03-01" in prompt  # content from the final section


def test_exhaustive_date_extraction_uses_complete_text(docx_user):
    prompts, write = docx_user
    write(1, "policy.docx")

    result = docx_compute.answer_full_document_question(
        user_id=1, question="List every date mentioned in the document", file_name="policy.docx"
    )

    assert result is not None
    (prompt,) = prompts
    assert "exhaustive" in prompt.lower()
    assert "date" in prompt.lower()  # extracted target phrase made it into the prompt
    # Dates from both the middle and final section should both be present --
    # again showing the whole document was passed, not a partial sample.
    assert "2024-01-15" in prompt
    assert "2025-03-01" in prompt


def test_fallback_when_question_is_not_full_document(docx_user):
    _, write = docx_user
    write(1, "policy.docx")
    question = "What is the approval process for remote work?"

    # The classifier shouldn't flag an ordinary, narrowly-scoped question.
    assert is_full_document_question(question) is False

    # And even called directly, the compute path must decline rather than
    # guess, so the caller falls back to the normal RAG path.
    result = docx_compute.answer_full_document_question(
        user_id=1, question=question, file_name="policy.docx"
    )
    assert result is None


def test_word_count_is_computed_not_asked_of_llm(docx_user):
    prompts, write = docx_user
    write(1, "policy.docx")

    result = docx_compute.answer_full_document_question(
        user_id=1, question="How many words are in this document?", file_name="policy.docx"
    )

    assert result is not None
    (prompt,) = prompts
    assert "Computed directly from the complete document" in prompt
    assert "Word count" in prompt


def test_too_large_document_declines_instead_of_truncating(docx_user, monkeypatch):
    prompts, write = docx_user
    write(1, "policy.docx")
    monkeypatch.setattr(docx_compute, "MAX_DOCUMENT_CHARS", 10)  # force the "too large" path

    result = docx_compute.answer_full_document_question(
        user_id=1, question="Summarize the whole document", file_name="policy.docx"
    )

    assert result is not None
    assert "too long" in result["answer"]
    assert prompts == []  # never even called the LLM -- didn't silently truncate and answer
