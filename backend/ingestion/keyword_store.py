"""
Manages a per-user BM25 keyword index. The chunked Document objects that back
FAISS are also persisted here (data/vector_index/{user_id}/chunks.pkl) so BM25
can be rebuilt on load without re-parsing the original source files.
"""

import os
import pickle
from typing import List, Optional

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_INDEX_DIR = os.path.join(BACKEND_DIR, "data", "vector_index")
CHUNKS_FILENAME = "chunks.pkl"


def _chunks_path(user_id: int) -> str:
    return os.path.join(VECTOR_INDEX_DIR, str(user_id), CHUNKS_FILENAME)


def save_chunks(chunks: List[Document], user_id: int) -> None:
    """Append newly ingested chunks to this user's persisted chunk list."""
    path = _chunks_path(user_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    existing = load_chunks(user_id) or []
    existing.extend(chunks)

    with open(path, "wb") as f:
        pickle.dump(existing, f)


def load_chunks(user_id: int) -> Optional[List[Document]]:
    """Return this user's persisted chunks, or None if none have been ingested yet."""
    path = _chunks_path(user_id)
    if not os.path.exists(path):
        return None

    with open(path, "rb") as f:
        return pickle.load(f)


def build_bm25_retriever(user_id: int) -> Optional[BM25Retriever]:
    """Build a BM25Retriever over this user's persisted chunks, or None if there are none."""
    chunks = load_chunks(user_id)
    if not chunks:
        return None
    return BM25Retriever.from_documents(chunks)


def remove_chunks_for_file(user_id: int, file_name: str) -> List[Document]:
    """Drop all persisted chunks belonging to `file_name` and return what remains.

    Used on document delete, alongside ingestion.vector_store.rebuild_faiss_index
    which rebuilds FAISS from the same remaining list.
    """
    chunks = load_chunks(user_id) or []
    remaining = [c for c in chunks if c.metadata.get("file_name") != file_name]

    path = _chunks_path(user_id)
    if remaining:
        with open(path, "wb") as f:
            pickle.dump(remaining, f)
    elif os.path.exists(path):
        os.remove(path)

    return remaining
