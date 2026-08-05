"""
Wraps the sentence-transformers embedding model used to embed document chunks and queries.
"""

from langchain_huggingface import HuggingFaceEmbeddings

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_embeddings_instance = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a process-wide cached HuggingFaceEmbeddings instance (model load is expensive)."""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embeddings_instance
