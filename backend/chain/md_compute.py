"""
Full-document query path for Markdown files: bypasses chunked/retrieved
context entirely for questions that need the complete document -- structural
facts (word count, header structure/table of contents) and exhaustive tasks
(a whole-document summary, "list every code snippet") that top-K retrieval
can't answer reliably from a partial sample of chunks.

Mirrors chain/docx_compute.py's shape and safety posture exactly -- see that
module's docstring for the full reasoning. Differences from DOCX/PDF:

  - No page_count operation: Markdown has no notion of pages.
  - No table_list operation: unlike DOCX/PDF, where tables are stored as a
    separate structured object that has to be deliberately extracted,
    Markdown pipe tables are already plain text right there in the source --
    there's no separate "structured form" to pull out, so no analogous
    extraction step is needed. A question about a Markdown table is already
    fully answerable from the raw text (via summarize/extract_all, or even
    normal RAG if it's small).
  - Headings come from loaders.document_loader.load_md_by_section(), reused
    as-is rather than reimplemented here -- same pattern as
    chain/docx_compute.py reusing load_docx_by_section().
"""

import logging
import os
import re
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from loaders.document_loader import load_md_by_section

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BACKEND_DIR, "data", "raw")

# Same reasoning/value as chain/docx_compute.py's MAX_DOCUMENT_CHARS.
MAX_DOCUMENT_CHARS = 24_000

ALLOWED_OPERATIONS = {"word_count", "heading_list", "summarize", "extract_all"}


# ---------------------------------------------------------------------------
# File resolution / loading
# ---------------------------------------------------------------------------

def list_user_md_files(user_id: int) -> List[str]:
    user_dir = os.path.join(RAW_DATA_DIR, str(user_id))
    if not os.path.isdir(user_dir):
        return []
    return sorted(f for f in os.listdir(user_dir) if f.lower().endswith(".md"))


def resolve_target_md_file(user_id: int, file_name: Optional[str]) -> Optional[str]:
    """Same rule as csv_compute/docx_compute/pdf_compute: use `file_name` if
    given, otherwise only proceed if there's exactly one .md for this user."""
    if file_name:
        return file_name if file_name.lower().endswith(".md") else None

    md_files = list_user_md_files(user_id)
    return md_files[0] if len(md_files) == 1 else None


@dataclass
class MDExtract:
    file_name: str
    full_text: str
    headings: List[str]
    word_count: int


def extract_document(user_id: int, file_name: str) -> Optional[MDExtract]:
    path = os.path.join(RAW_DATA_DIR, str(user_id), file_name)
    if not os.path.isfile(path):
        return None
    try:
        sections = load_md_by_section(path)
    except Exception:
        logger.exception("md_compute: failed to read %s", path)
        return None

    full_text = "\n\n".join(section.page_content for section in sections)
    headings = [s.metadata.get("section_heading") for s in sections if s.metadata.get("section_heading")]

    return MDExtract(file_name=file_name, full_text=full_text, headings=headings, word_count=len(full_text.split()))


# ---------------------------------------------------------------------------
# Plan building: question -> operation (content-independent, mirrors
# chain/docx_compute.py's build_document_plan)
# ---------------------------------------------------------------------------

@dataclass
class DocumentPlan:
    operation: str  # one of ALLOWED_OPERATIONS
    file_name: str
    extraction_target: str = "the requested items"


_WORD_COUNT_RE = re.compile(r"\bhow many words\b|\bword\s*count\b", re.IGNORECASE)
_HEADER_STRUCTURE_RE = re.compile(
    r"\btable of contents\b|\bheader(s)?\s+(list|structure|hierarchy)\b|\bheading(s)?\s+(list|structure|hierarchy)\b",
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
    if _HEADER_STRUCTURE_RE.search(question):
        return "heading_list"
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

def format_structural_fact(plan: DocumentPlan, doc: MDExtract) -> str:
    header = f"Computed directly from the complete document {doc.file_name} (not a retrieved excerpt)."

    if plan.operation == "word_count":
        return f"{header}\nWord count: {doc.word_count}"

    if plan.operation == "heading_list":
        if not doc.headings:
            return f"{header}\nThis document has no Markdown headings (no lines starting with #)."
        lines = [header, "Headings, in document order:"]
        lines.extend(f"  {i}. {h}" for i, h in enumerate(doc.headings, start=1))
        return "\n".join(lines)

    raise ValueError(f"format_structural_fact called with non-structural operation: {plan.operation}")


COMPUTE_PHRASING_PROMPT = PromptTemplate(
    input_variables=["question", "fact"],
    template=(
        "You are ContextIQ, answering a question about the user's uploaded Markdown document.\n\n"
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
    input_variables=["question", "full_text", "file_name"],
    template=(
        "You are ContextIQ. Below is the COMPLETE text of a Markdown document (not an excerpt "
        "or a retrieved sample) -- answer the question using it.\n\n"
        "Rules:\n"
        "- Base your answer only on the document text below.\n"
        "- If asked to summarize, cover the whole document, not just the beginning.\n"
        "- Preserve code exactly as it appears in code blocks if relevant to the answer.\n\n"
        "Document ({file_name}):\n{full_text}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    ),
)

EXTRACT_ALL_PROMPT = PromptTemplate(
    input_variables=["question", "target", "full_text", "file_name"],
    template=(
        "You are ContextIQ. Below is the COMPLETE text of a Markdown document (not an excerpt "
        "or a retrieved sample).\n\n"
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


def _too_large_answer(doc: MDExtract) -> str:
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
    """Try to answer `question` using the complete Markdown document,
    bypassing retrieval entirely. Returns a dict shaped like
    chain.rag_chain.run_rag_chain()'s return value on success, or None to
    signal "fall back to the normal RAG path".
    """
    target_file = resolve_target_md_file(user_id, file_name)
    if target_file is None:
        return None

    plan = build_document_plan(question, target_file)
    if plan is None:
        return None

    doc = extract_document(user_id, target_file)
    if doc is None:
        return None

    try:
        if plan.operation in ("word_count", "heading_list"):
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
        logger.exception("md_compute: failed answering %r for %r", plan, target_file)
        return None

    return {
        "answer": answer,
        "sources": [target_file],
        "rewritten_query": None,
    }
