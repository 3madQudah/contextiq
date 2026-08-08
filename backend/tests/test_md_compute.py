"""
Tests for Markdown header-hierarchy metadata (loaders/document_loader.py's
load_md_by_section) and the Markdown full-document query path
(chain/md_compute.py, chain/md_query_classifier.py).

The LLM call (chain.md_compute._llm) is monkeypatched the same way as the
CSV/DOCX/PDF compute tests -- see tests/test_docx_compute.py's module
docstring for the rationale. Markdown fixtures are plain text written
directly to disk, no external tooling needed.
"""

import pytest

from chain import md_compute
from chain.md_query_classifier import is_full_document_question
from loaders.document_loader import load_md_by_section


class _FakeResponse:
    def __init__(self, content):
        self.content = content


class _FakeLLM:
    def __init__(self, prompts):
        self._prompts = prompts

    def invoke(self, prompt):
        self._prompts.append(prompt)
        return _FakeResponse("STUBBED_ANSWER")


POLICY_MD = """# Policy Overview

This policy governs remote work arrangements company-wide.

## Eligibility

All full-time employees are eligible after 90 days of tenure.
The policy took effect on 2024-01-15.

## Approval Process

Managers must approve requests within 5 business days, a deadline last
revised on 2025-03-01.
"""


# ---------------------------------------------------------------------------
# Part C: header hierarchy preserved as chunk metadata
# ---------------------------------------------------------------------------

def test_md_header_hierarchy_preserved_as_metadata(tmp_path):
    path = tmp_path / "policy.md"
    path.write_text(POLICY_MD)

    sections = load_md_by_section(str(path))

    headings = [s.metadata.get("section_heading") for s in sections]
    assert headings == ["Policy Overview", "Eligibility", "Approval Process"]
    # Each section's text should be scoped to just that section, not bleed
    # into the next one.
    eligibility = next(s for s in sections if s.metadata["section_heading"] == "Eligibility")
    assert "90 days of tenure" in eligibility.page_content
    assert "5 business days" not in eligibility.page_content


def test_md_fenced_code_hash_not_treated_as_heading(tmp_path):
    content = "# Real Heading\n\nSome text.\n\n```\n# not a heading, inside a fence\n```\n\nMore text.\n"
    path = tmp_path / "with_code.md"
    path.write_text(content)

    sections = load_md_by_section(str(path))

    assert len(sections) == 1
    assert sections[0].metadata["section_heading"] == "Real Heading"
    assert "# not a heading, inside a fence" in sections[0].page_content


# ---------------------------------------------------------------------------
# Part B/D: full-document path
# ---------------------------------------------------------------------------

@pytest.fixture
def md_user(tmp_path, monkeypatch):
    monkeypatch.setattr(md_compute, "RAW_DATA_DIR", str(tmp_path))

    prompts = []
    monkeypatch.setattr(md_compute, "_llm", lambda: _FakeLLM(prompts))

    def _write(user_id: int, file_name: str, content: str = POLICY_MD) -> None:
        user_dir = tmp_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        (user_dir / file_name).write_text(content)

    return prompts, _write


def test_full_document_summary_uses_complete_text(md_user):
    prompts, write = md_user
    write(1, "policy.md")

    result = md_compute.answer_full_document_question(
        user_id=1, question="Please summarize the entire document", file_name="policy.md"
    )

    assert result is not None
    assert result["sources"] == ["policy.md"]
    assert result["answer"] == "STUBBED_ANSWER"
    (prompt,) = prompts
    assert "90 days of tenure" in prompt
    assert "revised on\n2025-03-01" in prompt or "revised on 2025-03-01" in prompt


def test_fallback_when_question_is_not_full_document(md_user):
    _, write = md_user
    write(1, "policy.md")
    question = "What is the approval process for remote work?"

    assert is_full_document_question(question) is False

    result = md_compute.answer_full_document_question(user_id=1, question=question, file_name="policy.md")
    assert result is None


def test_heading_list_is_computed_not_asked_of_llm(md_user):
    prompts, write = md_user
    write(1, "policy.md")

    result = md_compute.answer_full_document_question(
        user_id=1, question="What is the table of contents for this document?", file_name="policy.md"
    )

    assert result is not None
    (prompt,) = prompts
    assert "Policy Overview" in prompt
    assert "Eligibility" in prompt
    assert "Approval Process" in prompt


def test_too_large_document_declines_instead_of_truncating(md_user, monkeypatch):
    prompts, write = md_user
    write(1, "policy.md")
    monkeypatch.setattr(md_compute, "MAX_DOCUMENT_CHARS", 10)

    result = md_compute.answer_full_document_question(
        user_id=1, question="Summarize the whole document", file_name="policy.md"
    )

    assert result is not None
    assert "too long" in result["answer"]
    assert prompts == []
