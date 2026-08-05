"""
Splits loaded documents into smaller overlapping text chunks suitable for embedding.
"""

import os

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(
    documents,
    user_id: int,
    file_name: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
):
    """Split documents into chunks and tag each with user_id/file_name/file_type metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(documents)

    file_type = os.path.splitext(file_name)[1].lower().lstrip(".")
    for chunk in chunks:
        chunk.metadata.update(
            {
                "user_id": user_id,
                "file_name": file_name,
                "file_type": file_type,
            }
        )

    return chunks
