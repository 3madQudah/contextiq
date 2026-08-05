"""
Combines a user's FAISS (semantic) retriever and BM25 (keyword) retriever into
a single EnsembleRetriever for hybrid search.
"""

from typing import Optional, Tuple

from langchain_classic.retrievers import EnsembleRetriever

from ingestion.keyword_store import build_bm25_retriever
from ingestion.vector_store import load_faiss_index

# Relative weights for [FAISS (semantic), BM25 (keyword)] — tune these to experiment.
FAISS_WEIGHT = 0.5
BM25_WEIGHT = 0.5
DEFAULT_WEIGHTS = (FAISS_WEIGHT, BM25_WEIGHT)

# How many candidates each individual retriever pulls before the ensemble merges them.
TOP_K_PER_RETRIEVER = 8


def get_hybrid_retriever(
    user_id: int, weights: Tuple[float, float] = DEFAULT_WEIGHTS
) -> Optional[EnsembleRetriever]:
    """Return an EnsembleRetriever over this user's FAISS + BM25 indexes, or None
    if the user hasn't ingested any documents yet."""
    faiss_store = load_faiss_index(user_id)
    bm25_retriever = build_bm25_retriever(user_id)

    if faiss_store is None or bm25_retriever is None:
        return None

    faiss_retriever = faiss_store.as_retriever(search_kwargs={"k": TOP_K_PER_RETRIEVER})
    bm25_retriever.k = TOP_K_PER_RETRIEVER

    return EnsembleRetriever(
        retrievers=[faiss_retriever, bm25_retriever],
        weights=list(weights),
    )
