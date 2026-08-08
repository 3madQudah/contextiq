"""
Loads raw documents (PDF, DOCX, TXT, CSV, MD) from disk into LangChain Document
objects, dispatching to the appropriate loader based on file extension.
"""

import os
import re
from typing import List, Optional, Tuple

from docx import Document as DocxDocument
from langchain_community.document_loaders import CSVLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document

LOADER_MAP = {
    ".txt": TextLoader,
    ".csv": CSVLoader,
    # .pdf, .docx, .md deliberately aren't here -- each has its own loader
    # function below (load_pdf_with_scan_detection / load_docx_by_section /
    # load_md_by_section) so heading/section structure and scanned-PDF
    # detection survive into chunk metadata instead of being flattened away
    # by a generic loader before chunking ever runs.
}


# ---------------------------------------------------------------------------
# PDF: scanned/image-based detection
# ---------------------------------------------------------------------------

# A page with fewer non-whitespace extracted characters than this counts as
# "near-empty" -- a real text page rarely has this little, while a scanned
# image page (no text layer) extracts to "" or a stray OCR-adjacent artifact.
SCANNED_PDF_MIN_CHARS_PER_PAGE = 20

# If at least this fraction of a PDF's pages are near-empty, treat the whole
# file as scanned/image-based rather than a text PDF that merely has a few
# blank/mostly-image pages (a cover page, a divider, etc).
SCANNED_PDF_EMPTY_PAGE_FRACTION = 0.8


class ScannedPDFError(ValueError):
    """Raised when a .pdf appears to be scanned/image-based -- little to no
    extractable text layer -- instead of silently indexing an empty or
    near-empty document. See load_pdf_with_scan_detection()."""


def is_likely_scanned_pdf(page_texts: List[str]) -> bool:
    """True if `page_texts` (one extracted-text string per page, in any
    order) looks like a scanned/image-based PDF rather than one with a real
    text layer. Takes plain strings rather than Document/Page objects so
    both loaders.document_loader (LangChain Documents) and
    chain.pdf_compute (raw pypdf pages) can share this one check."""
    if not page_texts:
        return False
    near_empty = sum(1 for text in page_texts if len(text.strip()) < SCANNED_PDF_MIN_CHARS_PER_PAGE)
    return (near_empty / len(page_texts)) >= SCANNED_PDF_EMPTY_PAGE_FRACTION


def load_pdf_with_scan_detection(file_path: str) -> List[Document]:
    """Load a .pdf via PyPDFLoader (one Document per page), but raise
    ScannedPDFError instead of silently returning near-empty Documents when
    the file looks scanned/image-based.

    Before this check existed: PyPDFLoader/pypdf's extract_text() on an
    image-only page returns "" with no error or warning at all -- so a
    scanned PDF would sail through chunk_documents() (which splits "" into
    zero chunks) and build_faiss_index(), and the upload endpoint would
    report a normal 201 success with chunks_indexed: 0. The user would then
    get "I couldn't find anything relevant" forever for that file with no
    indication why. This surfaces that failure at upload time instead.

    OCR is not implemented here (would need the system `tesseract` binary --
    not a pip package -- plus the `pytesseract` and `PyMuPDF` pip packages,
    none of which are installed in this environment). The raised error names
    exactly what'd be needed to add it.
    """
    pages = PyPDFLoader(file_path).load()
    page_texts = [page.page_content for page in pages]

    if is_likely_scanned_pdf(page_texts):
        near_empty = sum(1 for text in page_texts if len(text.strip()) < SCANNED_PDF_MIN_CHARS_PER_PAGE)
        raise ScannedPDFError(
            f"{os.path.basename(file_path)} looks like a scanned/image-based PDF: "
            f"{near_empty} of {len(page_texts)} page(s) have no extractable text layer. "
            "OCR fallback is not currently enabled in ContextIQ. To add it: install the "
            "system `tesseract` binary (e.g. `brew install tesseract` on macOS -- this is "
            "a system package, not something `pip install` can provide) plus the "
            "`pytesseract` and `PyMuPDF` pip packages, then re-upload this file."
        )

    return pages


# ---------------------------------------------------------------------------
# DOCX: heading/section structure
# ---------------------------------------------------------------------------

# python-docx names built-in heading styles "Heading 1", "Heading 2", ...,
# and the first-page title style "Title". Custom/localized template styles
# won't match this and are treated as body text, same as before.
_DOCX_HEADING_STYLE_RE = re.compile(r"^(heading\s*\d+|title)$", re.IGNORECASE)


def load_docx_by_section(file_path: str) -> List[Document]:
    """Load a .docx file as one Document per section -- the run of paragraphs
    between one heading and the next -- tagging each with the heading text
    that introduces it as `section_heading` metadata.

    Replaces the previous Docx2txtLoader-based path, which returned a single
    Document holding the whole file as one flat text blob with no structural
    information at all: heading styles, section boundaries, everything was
    already gone before chunking ever ran. Text before the first heading (or
    a .docx with no headings at all) becomes one section with
    section_heading=None, so callers should always .get("section_heading")
    rather than assume the key is present with a non-None value.

    Downstream, ingestion.chunking.chunk_documents() further splits each
    section by chunk_size/chunk_overlap as usual -- RecursiveCharacterText
    Splitter.split_documents() deep-copies each source Document's metadata
    onto every chunk it produces from it, so section_heading survives that
    split intact without chunking.py needing any changes. chain/rag_chain.py's
    _format_chunk_header() surfaces it into what the LLM actually sees.
    """
    docx_file = DocxDocument(file_path)

    sections: List[Tuple[Optional[str], List[str]]] = []
    current_heading: Optional[str] = None
    current_paragraphs: List[str] = []

    def flush():
        if current_paragraphs:
            sections.append((current_heading, current_paragraphs))

    for paragraph in docx_file.paragraphs:
        style_name = paragraph.style.name if paragraph.style is not None else ""
        if _DOCX_HEADING_STYLE_RE.match((style_name or "").strip()):
            flush()
            # A blank heading paragraph keeps whatever heading was already
            # current rather than resetting to "no heading".
            current_heading = paragraph.text.strip() or current_heading
            current_paragraphs = []
        else:
            current_paragraphs.append(paragraph.text)
    flush()

    return [
        Document(page_content="\n".join(paragraphs).strip(), metadata={"section_heading": heading})
        for heading, paragraphs in sections
        if "\n".join(paragraphs).strip()
    ]


# ---------------------------------------------------------------------------
# Markdown: header hierarchy
# ---------------------------------------------------------------------------

# ATX-style headings only ("# Heading" through "###### Heading"), which
# covers the vast majority of real Markdown files including every fixture
# and example elsewhere in this project. Setext-style headings (a line of
# text underlined with === or ---) aren't matched -- a reasonable, documented
# gap rather than added complexity for a much less common style.
_MD_HEADING_RE = re.compile(r"^#{1,6}\s+(\S.*)$")
_MD_FENCE_RE = re.compile(r"^(```|~~~)")


def load_md_by_section(file_path: str) -> List[Document]:
    """Load a .md file as one Document per section -- the lines between one
    ATX heading (#, ##, ...) and the next -- tagging each with the heading
    text as `section_heading` metadata. Mirrors load_docx_by_section() above
    exactly, including its "text before the first heading -> section_heading
    None" fallback, and the same "no changes needed in chunking.py" note.

    Replaces the previous UnstructuredMarkdownLoader-based path, which
    returned a single Document with every heading marker stripped out --
    "## Kubernetes Rollout" became a plain sentence indistinguishable from
    body text, so no heading structure survived into chunk metadata at all.

    Lines inside fenced code blocks (``` or ~~~) are never treated as
    headings, so a shell/Python comment like "# some comment" inside a code
    sample doesn't get misread as a section break.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    sections: List[Tuple[Optional[str], List[str]]] = []
    current_heading: Optional[str] = None
    current_lines: List[str] = []
    in_fence = False

    def flush():
        if current_lines:
            sections.append((current_heading, current_lines))

    for line in lines:
        if _MD_FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            current_lines.append(line)
            continue

        heading_match = None if in_fence else _MD_HEADING_RE.match(line.rstrip("\n"))
        if heading_match:
            flush()
            current_heading = heading_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()

    return [
        Document(page_content="".join(lines).strip(), metadata={"section_heading": heading})
        for heading, lines in sections
        if "".join(lines).strip()
    ]


# ---------------------------------------------------------------------------

def load_document(file_path: str):
    """Load a single file on disk into a list of LangChain Document objects."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return load_pdf_with_scan_detection(file_path)
    if ext == ".docx":
        return load_docx_by_section(file_path)
    if ext == ".md":
        return load_md_by_section(file_path)

    loader_cls = LOADER_MAP.get(ext)
    if loader_cls is None:
        raise ValueError(f"Unsupported file type: {ext}")

    loader = loader_cls(file_path)
    return loader.load()
