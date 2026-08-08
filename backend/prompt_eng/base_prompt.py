"""
Shared building blocks for the per-file-type RAG prompts in this folder:
the system instructions common to every file type (citation rules, answer
formatting, no-hallucination-beyond-context) and the {history}/{context}/
{question} answer section every prompt ends with.

Each `<type>_prompt.py` module composes BASE_INSTRUCTIONS + its own
type-specific guidance + ANSWER_SECTION into one PromptTemplate, rather than
repeating these rules. DEFAULT_PROMPT_TEMPLATE (BASE_INSTRUCTIONS with no
added guidance) is the fallback for when retrieved context spans more than
one file type, so no single type's tailoring would fit — see
chain/rag_chain.py for where that fallback is chosen.
"""

from langchain_core.prompts import PromptTemplate

BASE_INSTRUCTIONS = (
    "You are ContextIQ, an assistant that answers questions using ONLY the "
    "context below, which was retrieved from the user's own uploaded documents.\n\n"
    "Each chunk of context is preceded by a [Source: <file name>] marker "
    "indicating which file it came from.\n\n"
    "Rules:\n"
    "- Answer strictly using the given context. If the context does not contain "
    "enough information to answer, say you don't know rather than guessing.\n"
    "- At the end of your answer, cite which file(s) the information came from, "
    "prefixed with \"Source:\", using the exact file name(s) taken from the "
    "[Source: ...] markers in the context above.\n"
    "- Use the prior conversation only to understand what the question refers "
    "to (e.g. pronouns like \"it\" or \"why\"); still answer strictly from the "
    "context above, not from the prior conversation."
)

ANSWER_SECTION = (
    "Prior conversation:\n{history}\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Answer:"
)

DEFAULT_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=BASE_INSTRUCTIONS + "\n\n" + ANSWER_SECTION,
)
