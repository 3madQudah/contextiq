"""
Lightweight keyword/pattern classifier that flags whether a question asked
against a DOCX-typed request needs the complete document rather than top-K
retrieved chunks: structural facts (word/page count, heading list, embedded
tables) and exhaustive tasks (a full-document summary, "list every date
mentioned") can't be answered reliably from a partial sample of chunks --
see prompt_eng/docx_prompt.py's "Scope honesty" guidance, which today can
only ask the LLM to hedge about this, not actually fix it.

Same style and same reasoning as chain/csv_query_classifier.py: regex-based,
not an LLM call, deliberately permissive -- a false positive here just means
chain/docx_compute.py's build_document_plan() declines to resolve a plan and
falls back to the normal RAG path, so an inexpensive, explainable heuristic
gate is preferable to a slower model call.
"""

import re

_WORD_COUNT_RE = re.compile(r"\bhow many words\b|\bword\s*count\b", re.IGNORECASE)
_PAGE_COUNT_RE = re.compile(r"\bhow many pages\b|\bpage\s*count\b", re.IGNORECASE)
_TABLE_OF_CONTENTS_RE = re.compile(
    r"\btable of contents\b|\bheading(s)?\s+(list|structure)\b", re.IGNORECASE
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
    """True if `question` needs the complete document rather than a handful
    of retrieved chunks -- structural facts (word/page count, heading list,
    embedded tables), exhaustive extraction ("list every date mentioned"),
    or an explicitly whole-document summary."""
    if any(pattern.search(question) for pattern in _ALL_PATTERNS):
        return True
    # "summarize" alone is too common/ambiguous to assume it means the whole
    # document (a question could reasonably be answered by summarizing just
    # the retrieved section) -- only trigger together with a whole-document
    # qualifier, mirroring chain/docx_compute.py's operation detection.
    return bool(_SUMMARIZE_RE.search(question) and _WHOLE_DOC_RE.search(question))
