"""
Document endpoints: upload documents, trigger ingestion (loading -> chunking ->
embedding -> vector store), and list a user's ingested documents.
"""

import os
import shutil

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from api.dependencies import get_current_user
from auth.models import User
from ingestion.chunking import chunk_documents
from ingestion.keyword_store import remove_chunks_for_file, save_chunks
from ingestion.vector_store import build_faiss_index, rebuild_faiss_index
from loaders.document_loader import load_document
from utils.helpers import is_supported_file

router = APIRouter()

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BACKEND_DIR, "data", "raw")


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_document(file: UploadFile, current_user: User = Depends(get_current_user)):
    if not is_supported_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed: .pdf, .docx, .txt, .csv, .md",
        )

    user_dir = os.path.join(RAW_DATA_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)

    file_path = os.path.join(user_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    documents = load_document(file_path)
    chunks = chunk_documents(documents, user_id=current_user.id, file_name=file.filename)
    build_faiss_index(chunks, user_id=current_user.id)
    save_chunks(chunks, user_id=current_user.id)

    return {"filename": file.filename, "chunks_indexed": len(chunks)}


@router.get("/")
def list_documents(current_user: User = Depends(get_current_user)):
    user_dir = os.path.join(RAW_DATA_DIR, str(current_user.id))
    if not os.path.isdir(user_dir):
        return {"documents": []}
    return {"documents": sorted(os.listdir(user_dir))}


@router.delete("/{file_name}")
def delete_document(file_name: str, current_user: User = Depends(get_current_user)):
    # Documents have no separate id/table in this phase — file_name is already
    # the identifier GET /api/documents/ lists them by, so it's the natural key
    # here rather than introducing a document-id concept just for this route.
    user_dir = os.path.join(RAW_DATA_DIR, str(current_user.id))
    file_path = os.path.join(user_dir, file_name)

    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    os.remove(file_path)

    remaining_chunks = remove_chunks_for_file(current_user.id, file_name)
    rebuild_faiss_index(remaining_chunks, current_user.id)

    return {"filename": file_name, "deleted": True, "remaining_chunks": len(remaining_chunks)}
