"""
RAG prompt tailored for CSV/tabular context: column-name awareness, row-level
reasoning, and aggregation awareness — selected when every retrieved chunk
for a question comes from a CSV file (see chain/rag_chain.py).
"""

from langchain_core.prompts import PromptTemplate

from prompt_eng.base_prompt import ANSWER_SECTION, BASE_INSTRUCTIONS

CSV_GUIDANCE = (
    "This context comes from CSV/tabular data. Each chunk contains one or "
    "more rows alongside their column headers. Apply the following when "
    "reasoning over it:\n\n"
    "Schema awareness:\n"
    "- Interpret every value through its column header — never infer a "
    "column's meaning from its position alone.\n"
    "- If the question asks about the file's structure (column names, row "
    "count, data types), answer only from what the retrieved context "
    "actually shows; do not extrapolate structure you haven't seen.\n\n"
    "Row-level reasoning:\n"
    "- Evaluate each visible row individually before answering — do not "
    "skim or answer from the first few rows alone.\n"
    "- For filters or lookups (e.g. 'employees over 30', 'find the row for "
    "X'), check every row in the retrieved context against the condition.\n\n"
    "Aggregation and computation:\n"
    "- Only compute a sum, average, count, min/max, or ranking (e.g. 'top 5') "
    "if the retrieved context contains the complete set of rows needed for "
    "an exact answer.\n"
    "- If the retrieved context is a partial sample of a larger dataset, do "
    "not present a computed aggregate as if it were exact. State plainly "
    "that the visible data is a subset and that the figure may not reflect "
    "the full dataset, rather than silently guessing or extrapolating.\n"
    "- Never fabricate a precise-looking number (e.g. an exact average or "
    "total) when the underlying rows to support it are not fully visible "
    "in the context.\n\n"
    "Precision:\n"
    "- Numeric answers must come directly from the data, not be rounded, "
    "estimated, or inferred from a general impression of the values."
)

CSV_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=BASE_INSTRUCTIONS + "\n\n" + CSV_GUIDANCE + "\n\n" + ANSWER_SECTION,
)