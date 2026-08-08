"""
Chat endpoint: accepts a user query, runs the RAG chain against the user's
hybrid index, and returns the generated answer (with source references),
persisting the exchange into the conversation's message history.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_owned_conversation_by_id
from auth.chat_models import Conversation, Message
from auth.database import get_db
from auth.models import User
from chain.csv_compute import answer_computational_question
from chain.csv_query_classifier import is_computational_question
from chain.docx_compute import answer_full_document_question as answer_docx_full_document_question
from chain.docx_query_classifier import is_full_document_question as is_docx_full_document_question
from chain.md_compute import answer_full_document_question as answer_md_full_document_question
from chain.md_query_classifier import is_full_document_question as is_md_full_document_question
from chain.pdf_compute import answer_full_document_question as answer_pdf_full_document_question
from chain.pdf_query_classifier import is_full_document_question as is_pdf_full_document_question
from chain.query_rewriter import DEFAULT_HISTORY_TURNS
from chain.rag_chain import run_rag_chain

router = APIRouter()

TITLE_MAX_LEN = 60

# file_type -> (classifier, full-document answer function), one pair per
# type with a full-document path (see chain/<type>_compute.py +
# chain/<type>_query_classifier.py for each). CSV isn't here since its
# computational path uses a differently-shaped classifier/answerer and is
# handled separately below.
FULL_DOCUMENT_HANDLERS = {
    "docx": (is_docx_full_document_question, answer_docx_full_document_question),
    "pdf": (is_pdf_full_document_question, answer_pdf_full_document_question),
    "md": (is_md_full_document_question, answer_md_full_document_question),
}


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None
    file_type: Optional[str] = None
    file_name: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    conversation_id: int
    rewritten_query: Optional[str] = None


def _recent_history(conversation: Conversation, turns: int = DEFAULT_HISTORY_TURNS) -> List[dict]:
    """Last `turns` user/assistant pairs as plain dicts, oldest first."""
    recent_messages = conversation.messages[-(turns * 2):]
    return [{"role": m.role, "content": m.content} for m in recent_messages]


@router.post("/ask", response_model=ChatResponse)
def ask(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.conversation_id is None:
        conversation = Conversation(
            user_id=current_user.id, title=payload.question[:TITLE_MAX_LEN]
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    else:
        conversation = get_owned_conversation_by_id(db, current_user.id, payload.conversation_id)

    history = _recent_history(conversation)

    # Persisted before the (possibly failing) LLM call — see the except block
    # below for why this message is deliberately never rolled back.
    user_message = Message(conversation_id=conversation.id, role="user", content=payload.question)
    db.add(user_message)
    db.commit()

    try:
        result = None
        # CSV-typed conversations get a shot at the computational path first
        # (exact pandas aggregation over the full file) before falling back
        # to the normal retrieval flow below -- see chain/csv_compute.py.
        if payload.file_type == "csv" and is_computational_question(payload.question):
            result = answer_computational_question(
                current_user.id, payload.question, file_name=payload.file_name
            )
        # Same pattern for DOCX/PDF/MD-typed conversations: structural/
        # exhaustive questions get a shot at the full-document path before
        # falling back to retrieval below -- see FULL_DOCUMENT_HANDLERS above
        # and each type's chain/<type>_compute.py.
        if result is None and payload.file_type in FULL_DOCUMENT_HANDLERS:
            classifier, answer_fn = FULL_DOCUMENT_HANDLERS[payload.file_type]
            if classifier(payload.question):
                result = answer_fn(current_user.id, payload.question, file_name=payload.file_name)
        if result is None:
            result = run_rag_chain(
                current_user.id,
                payload.question,
                history=history,
                file_type=payload.file_type,
                file_name=payload.file_name,
            )
    except Exception as exc:
        # The user's message above is already committed. We deliberately leave
        # it in place rather than deleting it: it's a real event ("the user
        # asked this") and the conversation should keep showing it happened,
        # even though it went unanswered — the user can see it and retry. What
        # we do NOT do is fabricate an assistant message to pair with it.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate an answer. Please try again.",
        ) from exc

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["answer"],
        sources=result["sources"],
    )
    db.add(assistant_message)

    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        conversation_id=conversation.id,
        rewritten_query=result.get("rewritten_query"),
    )
