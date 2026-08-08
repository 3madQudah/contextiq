"""
Full-document query path for PDF files: bypasses chunked/retrieved context
entirely for questions that need the complete document -- structural facts
(page count, word count, embedded outline/table of contents) and exhaustive
tasks (a whole-document summary, "list every date mentioned") that top-K
retrieval can't answer reliably from a partial sample of chunks.

Mirrors chain/docx_compute.py's shape and safety posture exactly -- see that
module's docstring for the full reasoning (compute-first-LLM-phrases-never-
recomputes for structural facts; full text handed to the LLM directly, under
an explicit character cap, for summarization/exhaustive extraction). This
docstring only calls out where PDF differs from DOCX:

  - Page count IS reliable here, unlike DOCX (see docx_compute.py's
    page_count handling for why DOCX's isn't) -- the PDF spec stores an
    actual page tree with a real page count as file structure, not a cached
    rendering estimate, and pypdf reads it directly from that structure.
  - "Headings" come from the PDF's embedded outline/bookmarks (pypdf's
    PdfReader.outline) when present -- many PDFs (scans, plain exports)
    don't have one at all, so this is reported honestly as "no outline"
    rather than an empty list pretending to be complete.
  - Table extraction is NOT implemented: pypdf (the library already in use
    here) doesn't expose tables as structured data at all, and no
    table-capable PDF library (e.g. pdfplumber, camelot) is installed. The
    classifier still recognizes "what tables" questions, but the answer is
    an honest "not supported yet, here's what it would take" rather than
    fabricated extraction -- flagged as a follow-up, per the task that
    introduced this module, rather than pulled into scope here.
  - Scanned/image-based PDFs (see loaders/document_loader.py's
    is_likely_scanned_pdf) are checked here too and short-circuit to an
    honest answer instead of summarizing/counting an empty text layer as if
    it were real content.
"""

import logging
import os
import re
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pypdf import PdfReader

from loaders.document_loader import is_likely_scanned_pdf

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BACKEND_DIR, "data", "raw")

# Same reasoning/value as chain/docx_compute.py's MAX_DOCUMENT_CHARS.
MAX_DOCUMENT_CHARS = 24_000

ALLOWED_OPERATIONS = {"word_count", "page_count", "heading_list", "table_list", "summarize", "extract_all"}


# ---------------------------------------------------------------------------
# File resolution / loading
# ---------------------------------------------------------------------------

def list_user_pdf_files(user_id: int) -> List[str]:
    user_dir = os.path.join(RAW_DATA_DIR, str(user_id))
    if not os.path.isdir(user_dir):
        return []
    return sorted(f for f in os.listdir(user_dir) if f.lower().endswith(".pdf"))


def resolve_target_pdf_file(user_id: int, file_name: Optional[str]) -> Optional[str]:
    """Same rule as csv_compute/docx_compute: use `file_name` if given,
    otherwise only proceed if there's exactly one PDF for this user."""
    if file_name:
        return file_name if file_name.lower().endswith(".pdf") else None

    pdf_files = list_user_pdf_files(user_id)
    return pdf_files[0] if len(pdf_files) == 1 else None


def _extract_outline_titles(outline) -> List[str]:
    """Flatten pypdf's (possibly nested, for sub-bookmarks) outline into a
    flat, in-order list of titles."""
    titles: List[str] = []
    for item in outline:
        if isinstance(item, list):
            titles.extend(_extract_outline_titles(item))
        else:
            title = getattr(item, "title", None)
            if title:
                titles.append(title)
    return titles


@dataclass
class PDFExtract:
    file_name: str
    full_text: str
    page_count: int
    word_count: int
    headings: List[str]
    outline_available: bool
    scanned: bool


def extract_document(user_id: int, file_name: str) -> Optional[PDFExtract]:
    path = os.path.join(RAW_DATA_DIR, str(user_id), file_name)
    if not os.path.isfile(path):
        return None

    try:
        reader = PdfReader(path)
        page_texts = [page.extract_text() or "" for page in reader.pages]
    except Exception:
        logger.exception("pdf_compute: failed to read %s", path)
        return None

    scanned = is_likely_scanned_pdf(page_texts)
    full_text = "\n\n".join(page_texts)
    outline = reader.outline or []

    return PDFExtract(
        file_name=file_name,
        full_text=full_text,
        page_count=len(reader.pages),
        word_count=len(full_text.split()),
        headings=_extract_outline_titles(outline),
        outline_available=bool(outline),
        scanned=scanned,
    )


# ---------------------------------------------------------------------------
# Plan building: question -> operation (content-independent, mirrors
# chain/docx_compute.py's build_document_plan exactly)
# ---------------------------------------------------------------------------

@dataclass
class DocumentPlan:
    operation: str  # one of ALLOWED_OPERATIONS
    file_name: str
    extraction_target: str = "the requested items"


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
_EXTRACT_TARGET_RE = re.compile(r"\b(?:list|extract)\s+(?:all|every)\s+([a-zA-Z][a-zA-Z\s]{0,40})", re.IGNORECASE)
_TARGET_TRIM_RE = re.compile(r"\bmentioned\b|\bin (the|this) document\b|[.?!]", re.IGNORECASE)


def _detect_operation(question: str) -> Optional[str]:
    """Priority order mirrors chain/docx_compute.py's _detect_operation."""
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
    """Same cosmetic best-effort extraction as chain/docx_compute.py's
    _extract_target_phrase -- see there for the reasoning."""
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

def format_structural_fact(plan: DocumentPlan, doc: PDFExtract) -> str:
    header = f"Computed directly from the complete document {doc.file_name} (not a retrieved excerpt)."

    if plan.operation == "word_count":
        return f"{header}\nWord count (extracted text across all {doc.page_count} page(s)): {doc.word_count}"

    if plan.operation == "page_count":
        # Unlike DOCX, this is a reliable structural fact -- see this
        # module's docstring -- so it's reported plainly, no caveat needed.
        return f"{header}\nPage count: {doc.page_count}"

    if plan.operation == "heading_list":
        if not doc.outline_available:
            return (
                f"{header}\nThis PDF has no embedded outline/table of contents/bookmarks "
                f"(common for scanned or simply-exported PDFs). It has {doc.page_count} page(s)."
            )
        lines = [header, "Outline/table of contents, in document order:"]
        lines.extend(f"  {i}. {h}" for i, h in enumerate(doc.headings, start=1))
        return "\n".join(lines)

    if plan.operation == "table_list":
        # See this module's docstring: not implemented -- pypdf doesn't
        # expose tables as structured data, and no table-capable PDF
        # library is installed. Honest non-answer, not fabricated extraction.
        return (
            f"{header}\nTable extraction isn't supported for PDFs yet -- the PDF library "
            "currently in use (pypdf) doesn't expose tables as structured data. Adding it "
            "would need an additional library such as pdfplumber or camelot, which isn't "
            "installed. Not answerable from this document right now."
        )

    raise ValueError(f"format_structural_fact called with non-structural operation: {plan.operation}")


COMPUTE_PHRASING_PROMPT = PromptTemplate(
    input_variables=["question", "fact"],
    template=(
        "You are ContextIQ, answering a question about the user's uploaded PDF document.\n\n"
        "A fact below has ALREADY been computed exactly, directly from the complete document "
        "-- not estimated, not sampled, not retrieved. Your only job is to phrase this fact as "
        "a clear, natural-language answer to the question.\n\n"
        "Rules:\n"
        "- Do NOT recompute, re-derive, or second-guess any number/list in the fact -- treat "
        "it as ground truth and report it exactly as given.\n"
        "- Do NOT add any items, numbers, or claims that are not present in the fact.\n"
        "- If the fact says something isn't available or isn't supported, say that plainly -- "
        "don't try to answer around it.\n"
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
    input_variables=["question", "full_text", "file_name"],
    template=(
        "You are ContextIQ. Below is the COMPLETE extracted text of a PDF (not an excerpt or "
        "a retrieved sample) -- answer the question using it.\n\n"
        "Rules:\n"
        "- Base your answer only on the document text below.\n"
        "- If asked to summarize, cover the whole document, not just the beginning.\n"
        "- PDF text extraction can include stray headers/footers/page numbers -- look past "
        "them rather than treating them as content.\n\n"
        "Document ({file_name}):\n{full_text}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    ),
)

EXTRACT_ALL_PROMPT = PromptTemplate(
    input_variables=["question", "target", "full_text", "file_name"],
    template=(
        "You are ContextIQ. Below is the COMPLETE extracted text of a PDF (not an excerpt or "
        "a retrieved sample).\n\n"
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


def _too_large_answer(doc: PDFExtract) -> str:
    return (
        f"{doc.file_name} is too long ({len(doc.full_text):,} characters, ~{doc.word_count:,} words "
        f"across {doc.page_count} pages) to summarize or exhaustively search in a single pass "
        f"(limit: {MAX_DOCUMENT_CHARS:,} characters). I can't reliably answer this for the whole "
        "document -- try asking about a specific section instead, or narrow the question."
    )


def _scanned_pdf_answer(doc: PDFExtract) -> str:
    return (
        f"{doc.file_name} appears to be a scanned/image-based PDF with no extractable text layer "
        f"(checked across {doc.page_count} page(s)), so I can't answer this from its content. "
        "OCR isn't currently enabled in ContextIQ -- see the upload error for what installing it "
        "would require."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def answer_full_document_question(
    user_id: int, question: str, file_name: Optional[str] = None
) -> Optional[dict]:
    """Try to answer `question` using the complete PDF document, bypassing
    retrieval entirely. Returns a dict shaped like
    chain.rag_chain.run_rag_chain()'s return value on success, or None to
    signal "fall back to the normal RAG path" -- ambiguous file, unreadable
    file, or a question that doesn't clearly match a full-document pattern.
    """
    target_file = resolve_target_pdf_file(user_id, file_name)
    if target_file is None:
        return None

    plan = build_document_plan(question, target_file)
    if plan is None:
        return None

    doc = extract_document(user_id, target_file)
    if doc is None:
        return None

    if doc.scanned:
        return {"answer": _scanned_pdf_answer(doc), "sources": [target_file], "rewritten_query": None}

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
        logger.exception("pdf_compute: failed answering %r for %r", plan, target_file)
        return None

    return {
        "answer": answer,
        "sources": [target_file],
        "rewritten_query": None,
    }
