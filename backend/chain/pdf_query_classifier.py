"""
Lightweight keyword/pattern classifier that flags whether a question asked
against a PDF-typed request needs the complete document rather than top-K
retrieved chunks: structural facts (page/word count, embedded outline/
table-of-contents) and exhaustive tasks (a full-document summary, "list
every date mentioned") can't be answered reliably from a partial sample of
chunks -- see prompt_eng/pdf_prompt.py's "Scope honesty" guidance, which
today can only ask the LLM to hedge about this, not actually fix it.

Same style, same reasoning, and (deliberately) near-identical patterns to
chain/docx_query_classifier.py -- see that module's docstring for why this
is regex-based rather than an LLM call. "What tables" is included here too
for symmetry with the DOCX classifier, even though chain/pdf_compute.py
currently answers it with an honest "not supported yet" fact rather than
real extraction -- see that module for why.
"""

import re

_WORD_COUNT_RE = re.compile(r"\bhow many words\b|\bword\s*count\b", re.IGNORECASE)
_PAGE_COUNT_RE = re.compile(r"\bhow many pages\b|\bpage\s*count\b", re.IGNORECASE)
_TABLE_OF_CONTENTS_RE = re.compile(
    r"\btable of contents\b|\boutline\b|\bheading(s)?\s+(list|structure)\b", re.IGNORECASE
)
_EMBEDDED_TABLES_RE = re.compile(
    r"\bwhat tables\b|\blist(ed)?\s+(the\s+)?tables\b|\bextract\s+(the\s+)?tables\b",
    re.IGNORECASE,
)
_EXHAUSTIVE_LIST_RE = re.compile(r"\b(list|extract)\s+(all|every)\b", re.IGNORECASE)
_WHOLE_DOC_RE = re.compile(r"\b(whole|entire|full|overall)\s+document\b", re.IGNORECASE)
_SUMMARIZE_RE = re.compile(r"\bsummar(y|ize|ise|izing|ising)\b", re.IGNORECASE)

_ALL_PATTERNS = (
    _WORD_COUNT_RE,
    _PAGE_COUNT_RE,
    _TABLE_OF_CONTENTS_RE,
    _EMBEDDED_TABLES_RE,
    _EXHAUSTIVE_LIST_RE,
)


def is_full_document_question(question: str) -> bool:
    """True if `question` needs the complete PDF rather than a handful of
    retrieved chunks -- structural facts (word/page count, outline/table of
    contents, embedded tables), exhaustive extraction ("list every date
    mentioned"), or an explicitly whole-document summary."""
    if any(pattern.search(question) for pattern in _ALL_PATTERNS):
        return True
    # Same reasoning as the DOCX classifier: "summarize" alone is too
    # common/ambiguous to assume whole-document scope on its own.
    return bool(_SUMMARIZE_RE.search(question) and _WHOLE_DOC_RE.search(question))
