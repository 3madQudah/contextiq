"""
Full-document query path for DOCX files: bypasses chunked/retrieved context
entirely for questions that need the complete document -- structural facts
(word count, heading list, embedded tables) and exhaustive tasks (a whole-
document summary, "list every date mentioned") that top-K retrieval can't
answer reliably from a partial sample of chunks.

Mirrors chain/csv_compute.py's shape and safety posture:
  - structural facts are computed directly (no LLM involved in the number),
    then handed to the LLM only to phrase them -- same "compute first, LLM
    phrases, never recomputes" split as the CSV path.
  - summarization/exhaustive-extraction genuinely need the LLM (there's no
    deterministic "compute" for a summary), so for those the full document
    text is handed to the LLM directly -- but only up to MAX_DOCUMENT_CHARS;
    past that we say so explicitly rather than silently truncating and
    answering as if the summary/extraction covered the whole document.
  - falls back (returns None) whenever a question, file, or fact can't be
    confidently resolved, exactly like the CSV path.
"""

import logging
import os
import re
from dataclasses import dataclass
from typing import List, Optional

from docx import Document as DocxDocument
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from loaders.document_loader import load_docx_by_section

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BACKEND_DIR, "data", "raw")

# ~4 chars/token is a standard rough estimate; 24,000 chars (~6k tokens) is
# comfortably within any modern LLM's context window with room left for the
# prompt/instructions/history/output, while still covering most real-world
# single documents users upload here. Tune if that turns out too tight.
MAX_DOCUMENT_CHARS = 24_000

ALLOWED_OPERATIONS = {"word_count", "page_count", "heading_list", "table_list", "summarize", "extract_all"}


# ---------------------------------------------------------------------------
# File resolution / loading
# ---------------------------------------------------------------------------

def list_user_docx_files(user_id: int) -> List[str]:
    user_dir = os.path.join(RAW_DATA_DIR, str(user_id))
    if not os.path.isdir(user_dir):
        return []
    return sorted(f for f in os.listdir(user_dir) if f.lower().endswith(".docx"))


def resolve_target_docx_file(user_id: int, file_name: Optional[str]) -> Optional[str]:
    """Same rule as csv_compute.resolve_target_csv_file: use `file_name` if
    given, otherwise only proceed if there's exactly one DOCX for this user
    -- with more than one and no explicit file_name we don't guess."""
    if file_name:
        return file_name if file_name.lower().endswith(".docx") else None

    docx_files = list_user_docx_files(user_id)
    return docx_files[0] if len(docx_files) == 1 else None


def _extract_tables(path: str) -> List[List[List[str]]]:
    """Each table as a list of rows, each row a list of cell strings, kept
    separate from paragraph text rather than flattened into prose.

    Note: python-docx's `Document.tables` returns every top-level table in
    document order, but *not* interleaved with `Document.paragraphs` -- so
    "table 2" here means the second table encountered, which may not match
    its position relative to surrounding narrative text. Fine for "what
    tables are in this document"-style questions (this module's only use of
    it); reconstructing true reading order would need walking the body XML
    directly and isn't done here.
    """
    docx_file = DocxDocument(path)
    return [[[cell.text for cell in row.cells] for row in table.rows] for table in docx_file.tables]


@dataclass
class DocumentExtract:
    file_name: str
    full_text: str
    headings: List[str]
    tables: List[List[List[str]]]
    word_count: int


def extract_document(user_id: int, file_name: str) -> Optional[DocumentExtract]:
    path = os.path.join(RAW_DATA_DIR, str(user_id), file_name)
    if not os.path.isfile(path):
        return None
    try:
        sections = load_docx_by_section(path)
        tables = _extract_tables(path)
    except Exception:
        logger.exception("docx_compute: failed to read %s", path)
        return None

    full_text = "\n\n".join(section.page_content for section in sections)
    headings = [s.metadata.get("section_heading") for s in sections if s.metadata.get("section_heading")]

    table_words = sum(len(cell.split()) for table in tables for row in table for cell in row)
    word_count = len(full_text.split()) + table_words

    return DocumentExtract(
        file_name=file_name, full_text=full_text, headings=headings, tables=tables, word_count=word_count
    )


# ---------------------------------------------------------------------------
# Plan building: question -> operation (content-independent, so this can run
# before the file is even loaded)
# ---------------------------------------------------------------------------

@dataclass
class DocumentPlan:
    operation: str  # one of ALLOWED_OPERATIONS
    file_name: str
    extraction_target: str = "the requested items"  # cosmetic only, see below


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
_EXTRACT_TARGET_RE = re.compile(r"\b(?:list|extract)\s+(?:all|every)\s+([a-zA-Z][a-zA-Z\s]{0,40})", re.IGNORECASE)
_TARGET_TRIM_RE = re.compile(r"\bmentioned\b|\bin (the|this) document\b|[.?!]", re.IGNORECASE)


def _detect_operation(question: str) -> Optional[str]:
    """Priority mirrors chain/csv_compute.py's _detect_operation: most
    specific/unambiguous patterns first. Word/page count and the two table-
    ish patterns are mutually exclusive by construction; exhaustive-list
    beats a bare "summarize" so "list every clause in the whole document"
    resolves to extraction, not a generic summary."""
    if _WORD_COUNT_RE.search(question):
        return "word_count"
    if _PAGE_COUNT_RE.search(question):
        return "page_count"
    if _TABLE_OF_CONTENTS_RE.search(question):
        return "heading_list"
    if _EMBEDDED_TABLES_RE.search(question):
        return "table_list"
    if _EXHAUSTIVE_LIST_RE.search(question):
        return "extract_all"
    if _SUMMARIZE_RE.search(question) and _WHOLE_DOC_RE.search(question):
        return "summarize"
    return None


def _extract_target_phrase(question: str) -> str:
    """Best-effort human-readable label for what an "extract_all" question
    wants (e.g. "dates" out of "list every date mentioned") -- purely
    cosmetic, used only to make the LLM prompt read naturally. The LLM also
    gets the original question verbatim, so a poor extraction here doesn't
    break the answer, just makes one prompt line slightly less polished."""
    match = _EXTRACT_TARGET_RE.search(question)
    if not match:
        return "the requested items"
    phrase = _TARGET_TRIM_RE.split(match.group(1))[0].strip()
    return phrase or "the requested items"


def build_document_plan(question: str, file_name: str) -> Optional[DocumentPlan]:
    operation = _detect_operation(question)
    if operation is None:
        return None
    extraction_target = _extract_target_phrase(question) if operation == "extract_all" else "the requested items"
    return DocumentPlan(operation=operation, file_name=file_name, extraction_target=extraction_target)


# ---------------------------------------------------------------------------
# Structural facts: computed directly, never left to the LLM to (re)derive
# ---------------------------------------------------------------------------

def format_structural_fact(plan: DocumentPlan, doc: DocumentExtract) -> str:
    header = f"Computed directly from the complete document {doc.file_name} (not a retrieved excerpt)."

    if plan.operation == "word_count":
        return f"{header}\nWord count (including any table cells): {doc.word_count}"

    if plan.operation == "page_count":
        # See chain/docx_compute.py module docstring / PR notes: .docx has no
        # authoritative, always-current page count -- it depends on print
        # layout (fonts, margins, printer) computed at render time, and any
        # cached <Pages> value in the file's app.xml can be stale or, for
        # files that were never opened in a full Word client (e.g. ones
        # generated programmatically), simply a placeholder unrelated to the
        # actual content. Rather than report that number as fact, say so and
        # offer word count as a useful substitute.
        return (
            f"{header}\nPage count is not reliably available for .docx files -- Word "
            "documents don't store an authoritative, always-current page count (it "
            "depends on print/rendering layout, not the file content). Word count "
            f"instead: {doc.word_count}."
        )

    if plan.operation == "heading_list":
        if not doc.headings:
            return f"{header}\nThis document has no headings (no Heading/Title-styled paragraphs)."
        lines = [header, "Headings, in document order:"]
        lines.extend(f"  {i}. {h}" for i, h in enumerate(doc.headings, start=1))
        return "\n".join(lines)

    if plan.operation == "table_list":
        if not doc.tables:
            return f"{header}\nThis document has no embedded tables."
        lines = [header, f"{len(doc.tables)} table(s) found:"]
        for i, table in enumerate(doc.tables, start=1):
            lines.append(f"  Table {i} ({len(table)} row(s)):")
            lines.extend(f"    {row}" for row in table)
        return "\n".join(lines)

    raise ValueError(f"format_structural_fact called with non-structural operation: {plan.operation}")


COMPUTE_PHRASING_PROMPT = PromptTemplate(
    input_variables=["question", "fact"],
    template=(
        "You are ContextIQ, answering a question about the user's uploaded DOCX document.\n\n"
        "A fact below has ALREADY been computed exactly, directly from the complete document "
        "-- not estimated, not sampled, not retrieved. Your only job is to phrase this fact as "
        "a clear, natural-language answer to the question.\n\n"
        "Rules:\n"
        "- Do NOT recompute, re-derive, or second-guess any number/list in the fact -- treat "
        "it as ground truth and report it exactly as given.\n"
        "- Do NOT add any items, numbers, or claims that are not present in the fact.\n"
        "- Be concise.\n\n"
        "Computed fact:\n{fact}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    ),
)

# ---------------------------------------------------------------------------
# Summarization / exhaustive extraction: genuinely needs the LLM over the
# full text -- there's no deterministic "compute" for these.
# ---------------------------------------------------------------------------

SUMMARIZE_PROMPT = PromptTemplate(
    input_variables=["question", "full_text"],
    template=(
        "You are ContextIQ. Below is the COMPLETE text of a document (not an excerpt or a "
        "retrieved sample) -- answer the question using it.\n\n"
        "Rules:\n"
        "- Base your answer only on the document text below.\n"
        "- If asked to summarize, cover the whole document, not just the beginning.\n\n"
        "Document ({file_name}):\n{full_text}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    ),
)

EXTRACT_ALL_PROMPT = PromptTemplate(
    input_variables=["question", "target", "full_text"],
    template=(
        "You are ContextIQ. Below is the COMPLETE text of a document (not an excerpt or a "
        "retrieved sample).\n\n"
        "Task: extract every instance of {target} mentioned anywhere in the document below, "
        "as a list. Go through the entire document, not just the beginning -- this must be "
        "exhaustive, not a sample. If none are found, say so explicitly.\n\n"
        "Document ({file_name}):\n{full_text}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    ),
)


def _llm() -> ChatGroq:
    return ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL_NAME, temperature=0)


def _too_large_answer(doc: DocumentExtract) -> str:
    return (
        f"{doc.file_name} is too long ({len(doc.full_text):,} characters, ~{doc.word_count:,} words) "
        f"to summarize or exhaustively search in a single pass (limit: {MAX_DOCUMENT_CHARS:,} characters). "
        "I can't reliably answer this for the whole document -- try asking about a specific "
        "section instead, or narrow the question."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def answer_full_document_question(
    user_id: int, question: str, file_name: Optional[str] = None
) -> Optional[dict]:
    """Try to answer `question` using the complete DOCX document, bypassing
    retrieval entirely. Returns a dict shaped like
    chain.rag_chain.run_rag_chain()'s return value on success, or None to
    signal "fall back to the normal RAG path" -- ambiguous file, unreadable
    file, or a question that doesn't clearly match a full-document pattern.
    """
    target_file = resolve_target_docx_file(user_id, file_name)
    if target_file is None:
        return None

    plan = build_document_plan(question, target_file)
    if plan is None:
        return None

    doc = extract_document(user_id, target_file)
    if doc is None:
        return None

    try:
        if plan.operation in ("word_count", "page_count", "heading_list", "table_list"):
            fact = format_structural_fact(plan, doc)
            answer = _llm().invoke(COMPUTE_PHRASING_PROMPT.format(question=question, fact=fact)).content.strip()
        elif plan.operation in ("summarize", "extract_all"):
            if len(doc.full_text) > MAX_DOCUMENT_CHARS:
                answer = _too_large_answer(doc)
            elif plan.operation == "summarize":
                prompt = SUMMARIZE_PROMPT.format(question=question, full_text=doc.full_text, file_name=doc.file_name)
                answer = _llm().invoke(prompt).content.strip()
            else:
                prompt = EXTRACT_ALL_PROMPT.format(
                    question=question,
                    target=plan.extraction_target,
                    full_text=doc.full_text,
                    file_name=doc.file_name,
                )
                answer = _llm().invoke(prompt).content.strip()
        else:  # pragma: no cover -- unreachable given ALLOWED_OPERATIONS/build_document_plan
            return None
    except Exception:
        logger.exception("docx_compute: failed answering %r for %r", plan, target_file)
        return None

    return {
        "answer": answer,
        "sources": [target_file],
        "rewritten_query": None,
    }
