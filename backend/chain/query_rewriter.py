"""
Rewrites a conversational follow-up ("and why?", "what about the second one?")
into a standalone question using recent chat history, so retrieval (FAISS/BM25)
has concrete terms to match against instead of bare pronouns.
"""

import logging
import os
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Deliberately a small/fast model for this cheap rewriting step, kept separate
# from GROQ_MODEL_NAME (the main answering model in chain/rag_chain.py) so the
# two can be tuned independently — e.g. a bigger answering model without
# paying that cost on every single-shot rewrite call too.
REWRITE_MODEL_NAME = os.getenv("GROQ_REWRITE_MODEL_NAME", "llama-3.1-8b-instant")

# How many prior user/assistant pairs count as "recent" — shared by the
# rewrite step and by rag_chain.py's answering prompt.
DEFAULT_HISTORY_TURNS = 3

REWRITE_PROMPT = PromptTemplate(
    input_variables=["history", "question"],
    template=(
        "Given the conversation history below and a follow-up question, rewrite the "
        "follow-up question so it can be understood on its own, without needing the "
        "history. Resolve pronouns and implicit references (\"it\", \"that\", \"the "
        "second one\", \"why\", etc.) into what they concretely refer to. If the "
        "follow-up question is already standalone, return it unchanged. Return ONLY "
        "the rewritten question — no preamble, no quotes.\n\n"
        "Conversation history:\n{history}\n\n"
        "Follow-up question: {question}\n\n"
        "Standalone question:"
    ),
)


def format_history(history: List[dict]) -> str:
    """Render [{"role": ..., "content": ...}, ...] as plain "role: content" lines."""
    return "\n".join(f"{turn['role']}: {turn['content']}" for turn in history)


def rewrite_query(question: str, history: Optional[List[dict]]) -> str:
    """Return a standalone version of `question`, or `question` unchanged if there's no history."""
    if not history:
        return question

    llm = ChatGroq(api_key=GROQ_API_KEY, model=REWRITE_MODEL_NAME, temperature=0)
    prompt = REWRITE_PROMPT.format(history=format_history(history), question=question)
    response = llm.invoke(prompt)
    rewritten = response.content.strip()

    logger.info("Query rewrite: %r -> %r", question, rewritten)

    return rewritten or question
