"""
Manages the FAISS vector index: creation, persistence to backend/data/vector_index,
loading, and adding new document chunks. Each user gets their own index directory
so retrieval never crosses between users' documents.
"""

import os
import shutil
from typing import List, Optional

from langchain_community.vectorstores import FAISS

from ingestion.embeddings import get_embeddings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_INDEX_DIR = os.path.join(BACKEND_DIR, "data", "vector_index")


def _index_path(user_id: int) -> str:
    return os.path.join(VECTOR_INDEX_DIR, str(user_id))


def build_faiss_index(chunks, user_id: int) -> FAISS:
    """Create the user's FAISS index if none exists yet, otherwise add chunks to it."""
    embeddings = get_embeddings()
    index_path = _index_path(user_id)

    if os.path.isdir(index_path):
        store = FAISS.load_local(
            index_path, embeddings, allow_dangerous_deserialization=True
        )
        store.add_documents(chunks)
    else:
        store = FAISS.from_documents(chunks, embeddings)

    os.makedirs(index_path, exist_ok=True)
    store.save_local(index_path)
    return store


def load_faiss_index(user_id: int):
    """Load a previously persisted FAISS index for this user, or None if it doesn't exist."""
    index_path = _index_path(user_id)
    if not os.path.isdir(index_path):
        return None

    embeddings = get_embeddings()
    return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)


def rebuild_faiss_index(chunks: List, user_id: int) -> Optional[FAISS]:
    """Replace the user's FAISS index from scratch using `chunks`.

    FAISS (as wrapped by langchain_community) has no delete-by-metadata: its
    only removal primitive is `.delete(ids=[...])` against its own internal
    vector ids, which we'd have to have captured and persisted at ingestion
    time (we don't). Rather than add that bookkeeping, we take the simpler,
    always-correct-by-construction route on document delete: re-embed and
    rebuild the whole index from the remaining persisted chunks. Cost: this is
    O(total remaining chunks for the user), not O(deleted file's chunks) — every
    delete re-embeds everything else that user has ever uploaded. Fine at small
    scale; if a user's corpus grows into the hundreds of documents, switching to
    FAISS.delete(ids=...) with an id-mapping persisted alongside chunks.pkl
    would be the next step.
    """
    index_path = _index_path(user_id)

    if not chunks:
        if os.path.isdir(index_path):
            shutil.rmtree(index_path)
        return None

    embeddings = get_embeddings()
    store = FAISS.from_documents(chunks, embeddings)
    os.makedirs(index_path, exist_ok=True)
    store.save_local(index_path)
    return store
