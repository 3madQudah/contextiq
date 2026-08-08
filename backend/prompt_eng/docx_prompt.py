"""
RAG prompt tailored for DOCX context: headings and structured sections —
selected when every retrieved chunk for a question comes from a DOCX file
(see chain/rag_chain.py).
"""

from langchain_core.prompts import PromptTemplate

from prompt_eng.base_prompt import ANSWER_SECTION, BASE_INSTRUCTIONS

DOCX_GUIDANCE = (
    "This context comes from Word documents, retrieved as chunks that may "
    "each carry a heading or section label. Apply the following when "
    "reasoning over it:\n\n"
    "Section awareness:\n"
    "- If a chunk includes a heading or section label, use it to scope your "
    "answer to that part of the document rather than treating all chunks as "
    "equally relevant.\n"
    "- If different sections address the question differently (e.g. "
    "conflicting or updated terms), state the distinction explicitly and "
    "attribute each part to its section, rather than blending them into one "
    "answer.\n\n"
    "Structure preservation:\n"
    "- Preserve numbered steps, lists, or clause structure from the source "
    "when it helps answer the question — don't collapse an ordered "
    "procedure or a multi-part clause into a single flattened sentence.\n\n"
    "Scope honesty:\n"
    "- Only answer from the sections actually present in the retrieved "
    "context. If the question asks about the document's overall structure, "
    "a full-document summary, or an exhaustive list (e.g. 'all dates "
    "mentioned', 'every clause'), and the context is a partial excerpt "
    "rather than the complete document, say so explicitly instead of "
    "presenting a partial answer as complete."
)

DOCX_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=BASE_INSTRUCTIONS + "\n\n" + DOCX_GUIDANCE + "\n\n" + ANSWER_SECTION,
)