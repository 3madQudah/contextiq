"""
RAG prompt tailored for plain-text context: little to no structure to lean
on, so the model should rely more on surrounding chunk context — selected
when every retrieved chunk for a question comes from a TXT file (see
chain/rag_chain.py).
"""

from langchain_core.prompts import PromptTemplate

from prompt_eng.base_prompt import ANSWER_SECTION, BASE_INSTRUCTIONS

TXT_GUIDANCE = (
    "This context comes from plain text files with no headings, formatting, "
    "or markup to signal structure. Apply the following:\n\n"
    "- Rely on the surrounding sentences within each chunk for meaning, "
    "since there are no headers or formatting cues to lean on instead.\n"
    "- Don't assume a section break or topic change unless the text itself "
    "clearly indicates one.\n"
    "- If the question asks for a full-document summary or an exhaustive "
    "extraction (e.g. 'every date mentioned') and the context is a partial "
    "excerpt rather than the complete file, say so explicitly instead of "
    "presenting a partial answer as complete."
)

TXT_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=BASE_INSTRUCTIONS + "\n\n" + TXT_GUIDANCE + "\n\n" + ANSWER_SECTION,
)