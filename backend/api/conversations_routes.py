"""
Conversation endpoints: list/create/view/rename/delete a user's chat threads.

Ownership enforcement is centralized in api.dependencies.get_owned_conversation
(a FastAPI dependency) — every route taking {conversation_id} depends on it so
a stale or foreign id always 404s and can't be forgotten on a future route.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_owned_conversation
from auth.chat_models import Conversation
from auth.database import get_db
from auth.models import User

router = APIRouter()


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[List[str]] = None
    created_at: datetime


class ConversationSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationDetail(ConversationSummary):
    messages: List[MessageResponse]


class ConversationCreateRequest(BaseModel):
    title: Optional[str] = None


class ConversationRenameRequest(BaseModel):
    title: str


def _to_summary(conversation: Conversation) -> ConversationSummary:
    return ConversationSummary(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(conversation.messages),
    )


@router.get("", response_model=List[ConversationSummary])
def list_conversations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [_to_summary(c) for c in conversations]


@router.post("", response_model=ConversationSummary, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = Conversation(
        user_id=current_user.id, title=payload.title or "New conversation"
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return _to_summary(conversation)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation: Conversation = Depends(get_owned_conversation)):
    summary = _to_summary(conversation)
    return ConversationDetail(
        **summary.model_dump(),
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                created_at=m.created_at,
            )
            for m in conversation.messages
        ],
    )


@router.patch("/{conversation_id}", response_model=ConversationSummary)
def rename_conversation(
    payload: ConversationRenameRequest,
    conversation: Conversation = Depends(get_owned_conversation),
    db: Session = Depends(get_db),
):
    conversation.title = payload.title
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conversation)
    return _to_summary(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation: Conversation = Depends(get_owned_conversation),
    db: Session = Depends(get_db),
):
    db.delete(conversation)
    db.commit()
