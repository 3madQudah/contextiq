"""
Lightweight keyword/pattern classifier that flags whether a question asked
against a Markdown-typed request needs the complete document rather than
top-K retrieved chunks: structural facts (word count, header structure/table
of contents) and exhaustive tasks (a full-document summary, "list every code
snippet") can't be answered reliably from a partial sample of chunks -- see
prompt_eng/md_prompt.py's "Scope honesty" guidance, which today can only ask
the LLM to hedge about this, not actually fix it.

Same style and reasoning as chain/csv_query_classifier.py and
chain/docx_query_classifier.py -- see those modules' docstrings. No page-
count or table-extraction patterns here: Markdown has no notion of pages,
and pipe tables are already plain text within the source (nothing separate
to extract the way DOCX/PDF tables are), so there's no analogous structural
fact to add for either.
"""

import re

_WORD_COUNT_RE = re.compile(r"\bhow many words\b|\bword\s*count\b", re.IGNORECASE)
_HEADER_STRUCTURE_RE = re.compile(
    r"\btable of contents\b|\bheader(s)?\s+(list|structure|hierarchy)\b|\bheading(s)?\s+(list|structure|hierarchy)\b",
    re.IGNORECASE,
)
_EXHAUSTIVE_LIST_RE = re.compile(r"\b(list|extract)\s+(all|every)\b", re.IGNORECASE)
_WHOLE_DOC_RE = re.compile(r"\b(whole|entire|full|overall)\s+document\b", re.IGNORECASE)
_SUMMARIZE_RE = re.compile(r"\bsummar(y|ize|ise|izing|ising)\b", re.IGNORECASE)

_ALL_PATTERNS = (_WORD_COUNT_RE, _HEADER_STRUCTURE_RE, _EXHAUSTIVE_LIST_RE)


def is_full_document_question(question: str) -> bool:
    """True if `question` needs the complete Markdown file rather than a
    handful of retrieved chunks -- structural facts (word count, header
    structure/table of contents), exhaustive extraction ("list every code
    snippet"), or an explicitly whole-document summary."""
    if any(pattern.search(question) for pattern in _ALL_PATTERNS):
        return True
    return bool(_SUMMARIZE_RE.search(question) and _WHOLE_DOC_RE.search(question))
