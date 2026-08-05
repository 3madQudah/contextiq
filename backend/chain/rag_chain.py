"""
Builds and runs the retrieval-augmented generation chain: rewrites conversational
follow-ups into a standalone query, retrieves relevant chunks via hybrid
(FAISS + BM25) search using that rewritten query, narrows them with optional
metadata filters, and generates an answer — using the ORIGINAL question plus
recent history — from the prompt template.
"""

import logging
import os
from typing import List, Optional

from dotenv import load_dotenv

# NOTE: ChatGroq calls the Groq API, which requires a free API key.
# Sign up at https://console.groq.com/keys and set GROQ_API_KEY in your .env file.
from langchain_groq import ChatGroq

from chain.hybrid_retriever import get_hybrid_retriever
from chain.metadata_filter import filter_documents
from chain.prompt_templates import RAG_PROMPT_TEMPLATE
from chain.query_rewriter import format_history, rewrite_query

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")

FETCH_K = 8
TOP_K = 4


def run_rag_chain(
    user_id: int,
    question: str,
    history: Optional[List[dict]] = None,
    file_type: Optional[str] = None,
    file_name: Optional[str] = None,
) -> dict:
    """Retrieve relevant chunks from the user's hybrid index and generate an answer.

    `history` is prior turns as [{"role": "user"|"assistant", "content": ...}, ...],
    oldest first. When non-empty it's used to (a) rewrite `question` into a
    standalone query for retrieval, and (b) give the LLM prior context — the
    ORIGINAL `question` (not the rewritten one) is what gets answered, so the
    reply reads naturally.
    """
    history = history or []

    rewritten_query = rewrite_query(question, history)
    if history:
        logger.info("Rewritten query for retrieval: %r -> %r", question, rewritten_query)

    retriever = get_hybrid_retriever(user_id)
    if retriever is None:
        return {
            "answer": "You haven't uploaded any documents yet. Upload a document before asking questions.",
            "sources": [],
            "rewritten_query": rewritten_query if history else None,
        }

    candidates = retriever.invoke(rewritten_query)[:FETCH_K]
    filtered = filter_documents(candidates, file_type=file_type, file_name=file_name)
    relevant_chunks = filtered[:TOP_K]

    if not relevant_chunks:
        return {
            "answer": "I couldn't find anything relevant to that question in your documents.",
            "sources": [],
            "rewritten_query": rewritten_query if history else None,
        }

    context = "\n\n".join(
        f"[Source: {chunk.metadata.get('file_name', 'unknown')}]\n{chunk.page_content}"
        for chunk in relevant_chunks
    )
    prompt = RAG_PROMPT_TEMPLATE.format(
        history=format_history(history) if history else "(none)",
        context=context,
        question=question,
    )

    llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL_NAME, temperature=0)
    response = llm.invoke(prompt)

    sources = sorted(
        {
            chunk.metadata.get("file_name")
            for chunk in relevant_chunks
            if chunk.metadata.get("file_name")
        }
    )

    return {
        "answer": response.content,
        "sources": sources,
        "rewritten_query": rewritten_query if history else None,
    }
