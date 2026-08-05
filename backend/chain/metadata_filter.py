"""
Post-retrieval filtering on chunk metadata (file_type, file_name).

Design note: per-user isolation is already handled by each user having their
own FAISS/BM25 index, so this filter only narrows results *within* a user's
own documents along optional extra dimensions.
"""

from typing import List, Optional

from langchain_core.documents import Document


def filter_documents(
    docs: List[Document],
    file_type: Optional[str] = None,
    file_name: Optional[str] = None,
) -> List[Document]:
    filtered = docs

    if file_type:
        normalized_type = file_type.lower().lstrip(".")
        filtered = [d for d in filtered if d.metadata.get("file_type") == normalized_type]

    if file_name:
        filtered = [d for d in filtered if d.metadata.get("file_name") == file_name]

    return filtered
