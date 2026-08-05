"""
Loads raw documents (PDF, DOCX, TXT, CSV, MD) from disk into LangChain Document
objects, dispatching to the appropriate loader based on file extension.
"""

import os

from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)

LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
    ".csv": CSVLoader,
    ".md": UnstructuredMarkdownLoader,
}


def load_document(file_path: str):
    """Load a single file on disk into a list of LangChain Document objects."""
    ext = os.path.splitext(file_path)[1].lower()
    loader_cls = LOADER_MAP.get(ext)
    if loader_cls is None:
        raise ValueError(f"Unsupported file type: {ext}")

    loader = loader_cls(file_path)
    return loader.load()
