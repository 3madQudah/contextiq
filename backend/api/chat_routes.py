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
from chain.query_rewriter import DEFAULT_HISTORY_TURNS
from chain.rag_chain import run_rag_chain

router = APIRouter()

TITLE_MAX_LEN = 60


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
