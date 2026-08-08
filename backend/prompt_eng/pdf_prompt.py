"""
RAG prompt tailored for PDF context: inconsistent extracted formatting and
optional page references — selected when every retrieved chunk for a
question comes from a PDF file (see chain/rag_chain.py).
"""

from langchain_core.prompts import PromptTemplate

from prompt_eng.base_prompt import ANSWER_SECTION, BASE_INSTRUCTIONS

PDF_GUIDANCE = (
    "This context comes from PDF documents, extracted page by page. "
    "Extraction can be imperfect — stray headers, footers, or page numbers "
    "may appear mixed into the text, and layout like tables or multi-column "
    "text may have lost its original structure. Apply the following:\n\n"
    "Noise handling:\n"
    "- Look past stray header/footer/page-number artifacts rather than "
    "treating them as content.\n"
    "- If a page number is visibly printed in the context, you may cite it "
    "(e.g. \"on page 3\") to help the user locate the information — never "
    "invent one if none is visible.\n\n"
    "Structural ambiguity:\n"
    "- If lost formatting makes part of the context ambiguous (e.g. a table "
    "that reads like a run-on list of numbers), say so rather than guessing "
    "at structure that isn't clearly there.\n\n"
    "Document-type awareness:\n"
    "- If the content resembles a specific document type (invoice, contract, "
    "research paper, report), use the terminology and structure typical of "
    "that type to interpret it — e.g. treat a trailing total-looking figure "
    "on an invoice as the total, not just another number.\n\n"
    "Scope honesty:\n"
    "- Only answer from the pages/sections actually present in the retrieved "
    "context. If the question asks about the document's overall structure, "
    "a full-document summary, or an exhaustive list (e.g. 'every date "
    "mentioned', 'all tables'), and the context is a partial excerpt, say so "
    "explicitly instead of presenting a partial answer as complete."
)

PDF_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=BASE_INSTRUCTIONS + "\n\n" + PDF_GUIDANCE + "\n\n" + ANSWER_SECTION,
)