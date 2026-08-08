"""
Per-file-type prompt templates, collected into one registry so the rest of
the app selects a prompt via PROMPT_REGISTRY[file_type] instead of an
if/elif chain. Keys match the `file_type` metadata tag chunks are stored
with (see ingestion/chunking.py) — the file extension, lowercased, no dot —
plus "sql" for the text-to-SQL feature.

Retrieved context doesn't always resolve to a single file type (e.g. a
question answered from a mix of PDF and CSV chunks) — callers should look
this up with .get() and fall back to prompt_eng.base_prompt.DEFAULT_PROMPT_TEMPLATE
rather than assume a key is always present.
"""

from prompt_eng.csv_prompt import CSV_PROMPT_TEMPLATE
from prompt_eng.docx_prompt import DOCX_PROMPT_TEMPLATE
from prompt_eng.md_prompt import MD_PROMPT_TEMPLATE
from prompt_eng.pdf_prompt import PDF_PROMPT_TEMPLATE
from prompt_eng.sql_prompt import SQL_PROMPT_TEMPLATE
from prompt_eng.txt_prompt import TXT_PROMPT_TEMPLATE

PROMPT_REGISTRY = {
    "csv": CSV_PROMPT_TEMPLATE,
    "pdf": PDF_PROMPT_TEMPLATE,
    "docx": DOCX_PROMPT_TEMPLATE,
    "txt": TXT_PROMPT_TEMPLATE,
    "md": MD_PROMPT_TEMPLATE,
    "sql": SQL_PROMPT_TEMPLATE,
}
