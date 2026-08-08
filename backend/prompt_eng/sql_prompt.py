"""
Prompts for the text-to-SQL feature (chain/sql_chain.py): natural-language-
to-SQL translation with schema awareness and a SELECT-only reminder, plus a
second prompt for summarizing query results in plain language. Kept in this
folder alongside the per-file-type RAG prompts as one place for all prompt
engineering, even though the SQL feature has no embeddings/retrieval.

Only SQL_PROMPT_TEMPLATE (the NL-to-SQL step) is registered under "sql" in
PROMPT_REGISTRY — SQL_ANSWER_PROMPT_TEMPLATE (the results summarizer) isn't
selected by file_type, so chain/sql_chain.py imports it directly by name.
"""

from langchain_core.prompts import PromptTemplate

SQL_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["db_type", "schema", "question"],
    template=(
        "You are a SQL generator for a {db_type} database. You are given the "
        "database schema and a natural-language question. Output EXACTLY ONE SQL "
        "SELECT statement that answers the question, and nothing else — no "
        "explanation, no markdown code fences, no multiple statements.\n\n"
        "Rules:\n"
        "- You may only ever produce a single read-only SELECT statement. You are "
        "not permitted to modify data in any way (no INSERT, UPDATE, DELETE, DROP, "
        "ALTER, or any other write) — this applies even if the question explicitly "
        "asks for a modification. If the question asks for a data modification or "
        "anything else a SELECT cannot do, respond with exactly: SELECT 1 WHERE 1=0\n"
        "- Use only the tables and columns listed in the schema below; never "
        "invent table or column names.\n"
        "- Do not wrap the SQL in markdown or add any commentary before or after it.\n\n"
        "Schema:\n{schema}\n\n"
        "Question: {question}\n\n"
        "SQL:"
    ),
)

SQL_ANSWER_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["question", "columns", "rows", "truncated_note"],
    template=(
        "You answer questions about the results of a SQL query, in plain language.\n\n"
        "Question: {question}\n\n"
        "Result columns: {columns}\n"
        "Result rows:\n{rows}\n"
        "{truncated_note}\n\n"
        "Give a concise, direct natural-language answer to the question using only "
        "this data. If there are no rows, say so plainly rather than guessing.\n\n"
        "Answer:"
    ),
)
