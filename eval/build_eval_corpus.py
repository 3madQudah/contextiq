"""
One-time fixture builder for the retrieval eval set.

The dev environment did not have enough indexed data to evaluate retrieval
across all 5 supported file types (only .txt/.csv/.md existed, 6 chunks
total, no .pdf or .docx). This script ingests a small synthetic corpus
(eval/fixtures/*) covering all 5 types into a dedicated eval user
(EVAL_USER_ID, see eval/config.py) so run_eval.py has something real to
retrieve against.

Importantly, this does NOT reimplement or modify ingestion: it calls the
exact same functions api/documents_routes.py's upload_document() calls
(load_document -> chunk_documents -> build_faiss_index -> save_chunks).
It is a fixture-loading script, not a change to app logic, and it only
touches data/raw/<EVAL_USER_ID>/ and data/vector_index/<EVAL_USER_ID>/ --
your real users' indexes are untouched.

Run once from the eval/ directory:
    cd eval && python3 build_eval_corpus.py
Safe to re-run: it wipes and rebuilds only the eval user's own data.
"""

import os
import shutil
import sys

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(os.path.dirname(EVAL_DIR), "backend")
sys.path.insert(0, BACKEND_DIR)

from config import EVAL_USER_ID  # noqa: E402

from ingestion.chunking import chunk_documents  # noqa: E402
from ingestion.keyword_store import save_chunks  # noqa: E402
from ingestion.vector_store import build_faiss_index  # noqa: E402
from loaders.document_loader import load_document  # noqa: E402

FIXTURES_DIR = os.path.join(EVAL_DIR, "fixtures")
RAW_DIR = os.path.join(BACKEND_DIR, "data", "raw", str(EVAL_USER_ID))
INDEX_DIR = os.path.join(BACKEND_DIR, "data", "vector_index", str(EVAL_USER_ID))

# Ingested in a fixed order so chunk indices (assigned in run_eval.py by
# position within each file) are reproducible across rebuilds.
FIXTURE_FILES = [
    "product_faq.txt",
    "release_notes.txt",
    "deployment_guide.md",
    "api_reference.md",
    "quarterly_sales.csv",
    "employee_roster.csv",
    "board_meeting_minutes.pdf",
    "security_audit_report.pdf",
    "employee_handbook.docx",
    "onboarding_checklist.docx",
]


def main():
    # Start clean so re-runs don't duplicate chunks.
    for path in (RAW_DIR, INDEX_DIR):
        if os.path.isdir(path):
            shutil.rmtree(path)
    os.makedirs(RAW_DIR, exist_ok=True)

    total_chunks = 0
    for file_name in FIXTURE_FILES:
        src = os.path.join(FIXTURES_DIR, file_name)
        dst = os.path.join(RAW_DIR, file_name)
        shutil.copyfile(src, dst)

        documents = load_document(dst)
        chunks = chunk_documents(documents, user_id=EVAL_USER_ID, file_name=file_name)
        build_faiss_index(chunks, user_id=EVAL_USER_ID)
        save_chunks(chunks, user_id=EVAL_USER_ID)
        total_chunks += len(chunks)
        print(f"  ingested {file_name}: {len(chunks)} chunk(s)")

    print(f"\nDone. {total_chunks} chunks indexed for eval user_id={EVAL_USER_ID}.")


if __name__ == "__main__":
    main()
