"""
RAG prompt tailored for Markdown context: headers, code blocks, and lists as
structure signals — selected when every retrieved chunk for a question
comes from a Markdown file (see chain/rag_chain.py).
"""

from langchain_core.prompts import PromptTemplate

from prompt_eng.base_prompt import ANSWER_SECTION, BASE_INSTRUCTIONS

MD_GUIDANCE = (
    "This context comes from Markdown files, where headers (#), lists, and "
    "code blocks (```) carry real structure. Apply the following:\n\n"
    "Header hierarchy:\n"
    "- If a chunk carries a heading (via metadata or an inline # marker), "
    "use it to scope your answer to that section rather than treating all "
    "chunks as equally relevant.\n"
    "- Understand nesting — a subsection belongs under the heading above it "
    "— when the question depends on that relationship.\n\n"
    "Code and lists:\n"
    "- If the answer includes code, preserve it exactly as it appears in a "
    "code block rather than paraphrasing or reformatting it.\n"
    "- Treat list items as discrete points rather than merging them into "
    "continuous prose when the question asks for specifics.\n\n"
    "Scope honesty:\n"
    "- Only answer from the sections actually present in the retrieved "
    "context. If the question asks for the document's full header structure, "
    "a complete summary, or an exhaustive extraction (e.g. 'all code "
    "snippets', 'every link'), and the context is a partial excerpt, say so "
    "explicitly instead of presenting a partial answer as complete."
)

MD_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=BASE_INSTRUCTIONS + "\n\n" + MD_GUIDANCE + "\n\n" + ANSWER_SECTION,
)