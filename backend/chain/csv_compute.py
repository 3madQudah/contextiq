"""
Computational query path for CSV files: bypasses chunked/retrieved context
entirely and answers aggregation questions ("what's the average of column X",
"top 5 by Y", "how many rows have Z") by loading the raw uploaded CSV in
full via pandas and computing the exact answer.

This exists because the RAG path answers from whatever chunks retrieval
happened to return -- a partial sample of a CSV's rows -- so aggregates
computed that way can silently be wrong (see prompt_eng/csv_prompt.py's
CSV_GUIDANCE, which tells the LLM to hedge rather than guess when that
happens; this module is the fix that lets ContextIQ answer for real instead).

Safety: the LLM is NEVER asked to write or execute pandas/exec code, and no
user text ever reaches eval()/exec()/DataFrame.query(). build_compute_plan()
resolves the question to a plan built ONLY from (a) a fixed set of 8
whitelisted operation names and (b) column names that literally exist in the
loaded DataFrame -- both closed, validated sets, never raw user text. execute_
plan() then dispatches that plan through a fixed set of pandas method calls
(.sum/.mean/.median/.max/.min/.count/.groupby/.sort_values.head). The LLM is
only invoked afterward, to phrase the already-computed, already-correct
result in natural language -- it cannot change the number.

Falls back to the RAG path (by returning None) whenever anything can't be
confidently resolved: no CSV file, an unparseable CSV, an operation we can't
identify, or a column we can't confidently match -- see
answer_computational_question().
"""

import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BACKEND_DIR, "data", "raw")

ALLOWED_OPERATIONS = {"sum", "mean", "median", "count", "max", "min", "top_n", "bottom_n"}


# ---------------------------------------------------------------------------
# File resolution / loading
# ---------------------------------------------------------------------------

def list_user_csv_files(user_id: int) -> List[str]:
    """CSV file names in this user's raw upload directory, or [] if none."""
    user_dir = os.path.join(RAW_DATA_DIR, str(user_id))
    if not os.path.isdir(user_dir):
        return []
    return sorted(f for f in os.listdir(user_dir) if f.lower().endswith(".csv"))


def resolve_target_csv_file(user_id: int, file_name: Optional[str]) -> Optional[str]:
    """Pick which CSV file to compute over.

    If `file_name` is given, use it (must actually be a .csv). Otherwise,
    only proceed if the user has exactly one CSV file -- with more than one
    and no explicit file_name, we can't know which one the question means,
    so we deliberately don't guess (returns None -> caller falls back to RAG).
    """
    if file_name:
        return file_name if file_name.lower().endswith(".csv") else None

    csv_files = list_user_csv_files(user_id)
    return csv_files[0] if len(csv_files) == 1 else None


def load_csv_dataframe(user_id: int, file_name: str) -> Optional[pd.DataFrame]:
    """Load a user's CSV in full, or None if it's missing/unreadable.

    keep_default_na=False + na_values=[""]: pandas' default NA sentinel list
    includes plain data values that show up constantly in real CSVs -- "NA"
    (e.g. North America as a region code), "NULL", "None" -- and silently
    turns matching cells into NaN. That's especially dangerous here because
    DataFrame.groupby() drops NaN group keys by default, so a region/category
    literally named "NA" would silently vanish from every group-by aggregate
    with no error. Only genuinely empty cells are treated as missing.
    """
    path = os.path.join(RAW_DATA_DIR, str(user_id), file_name)
    if not os.path.isfile(path):
        return None
    try:
        return pd.read_csv(path, keep_default_na=False, na_values=[""])
    except Exception:
        logger.exception("csv_compute: failed to read %s", path)
        return None


# ---------------------------------------------------------------------------
# Plan building: question -> ComputePlan, using only regex + real column names
# ---------------------------------------------------------------------------

@dataclass
class ComputePlan:
    operation: str  # one of ALLOWED_OPERATIONS
    value_column: Optional[str]  # numeric column to aggregate; None only for plain count
    group_by_column: Optional[str]
    n: Optional[int]  # for top_n / bottom_n
    file_name: str


_TOP_N_RE = re.compile(r"\btop\s+(\d+)\b", re.IGNORECASE)
_BOTTOM_N_RE = re.compile(r"\bbottom\s+(\d+)\b", re.IGNORECASE)
_MEAN_RE = re.compile(r"\b(average|mean)\b", re.IGNORECASE)
_MEDIAN_RE = re.compile(r"\bmedian\b", re.IGNORECASE)
_SUM_RE = re.compile(r"\b(total|sum)\b", re.IGNORECASE)
_COUNT_RE = re.compile(r"\b(how many|number of|count)\b", re.IGNORECASE)
_MAX_RE = re.compile(r"\b(highest|largest|greatest|maximum|max)\b", re.IGNORECASE)
_MIN_RE = re.compile(r"\b(lowest|smallest|least|minimum|min)\b", re.IGNORECASE)


def _detect_operation(question: str):
    """Return (operation, n) with n only set for top_n/bottom_n. Priority:
    "top/bottom N" (most specific -- has a literal count attached) beats
    max/min (superlative single-row intent) beats mean/median beats sum beats
    plain count, since a question can plausibly contain more than one of
    these words (e.g. "highest total revenue")."""
    m = _TOP_N_RE.search(question)
    if m:
        return "top_n", int(m.group(1))
    m = _BOTTOM_N_RE.search(question)
    if m:
        return "bottom_n", int(m.group(1))
    if _MAX_RE.search(question):
        return "max", None
    if _MIN_RE.search(question):
        return "min", None
    if _MEAN_RE.search(question):
        return "mean", None
    if _MEDIAN_RE.search(question):
        return "median", None
    if _SUM_RE.search(question):
        return "sum", None
    if _COUNT_RE.search(question):
        return "count", None
    return None, None


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _find_named_column(question_norm: str, columns: List[str]) -> Optional[str]:
    """Which of `columns` is mentioned by name in the (normalized) question,
    preferring the longest/most-specific match if more than one fits."""
    matches = []
    for col in columns:
        col_norm = _normalize(col)
        if col_norm and re.search(rf"\b{re.escape(col_norm)}\b", question_norm):
            matches.append(col)
    if not matches:
        return None
    return max(matches, key=lambda c: len(_normalize(c)))


def _find_group_by_column(question_norm: str, columns: List[str]) -> Optional[str]:
    """Which of `columns` follows "by "/"per " in the (normalized) question,
    e.g. "revenue by region" or "count per department"."""
    matches = []
    for col in columns:
        col_norm = _normalize(col)
        if not col_norm:
            continue
        if re.search(rf"\bby\s+{re.escape(col_norm)}\b", question_norm) or re.search(
            rf"\bper\s+{re.escape(col_norm)}\b", question_norm
        ):
            matches.append(col)
    if not matches:
        return None
    return max(matches, key=lambda c: len(_normalize(c)))


def build_compute_plan(question: str, df: pd.DataFrame, file_name: str) -> Optional[ComputePlan]:
    """Resolve `question` into a ComputePlan, or None if any part of it
    (operation, target column) can't be confidently determined -- callers
    treat None as "fall back to RAG", so it's safe/expected to be
    conservative here rather than guess."""
    operation, n = _detect_operation(question)
    if operation is None:
        return None
    if operation in ("top_n", "bottom_n") and not n:
        return None

    question_norm = _normalize(question)
    all_columns = list(df.columns)
    numeric_columns = [c for c in all_columns if pd.api.types.is_numeric_dtype(df[c])]

    # "by "/"per " means group-by for aggregate ops ("revenue by region") but
    # means "ranked by" for top/bottom-N ("top 5 by revenue") -- that's the
    # ranking column, i.e. value_column, handled below, not a group-by.
    if operation in ("top_n", "bottom_n"):
        group_by_column = None
    else:
        group_by_column = _find_group_by_column(question_norm, all_columns)

    if operation == "count":
        value_column = None
    else:
        value_column = _find_named_column(question_norm, numeric_columns)
        if value_column is None and len(numeric_columns) == 1:
            # Only one numeric column exists at all -- safe to assume that's
            # the one being asked about even if it wasn't named explicitly.
            value_column = numeric_columns[0]
        if value_column is None:
            return None

    return ComputePlan(
        operation=operation,
        value_column=value_column,
        group_by_column=group_by_column,
        n=n,
        file_name=file_name,
    )


# ---------------------------------------------------------------------------
# Plan execution: fixed dispatch over real pandas methods, no eval/exec/query
# ---------------------------------------------------------------------------

def _to_python(value: Any) -> Any:
    """Unwrap numpy scalars (e.g. numpy.int64) to plain Python types so the
    result is cleanly JSON-serializable / string-formattable."""
    return value.item() if hasattr(value, "item") else value


def execute_plan(plan: ComputePlan, df: pd.DataFrame) -> Dict[str, Any]:
    """Run `plan` against `df` and return a structured, exact result.
    `plan.operation` is guaranteed by build_compute_plan() to be one of
    ALLOWED_OPERATIONS, and `plan.value_column`/`plan.group_by_column` are
    guaranteed to be real columns of `df` -- so every attribute/column access
    below is against a closed, pre-validated set, never raw user input."""
    assert plan.operation in ALLOWED_OPERATIONS

    if plan.group_by_column and plan.operation in ("sum", "mean", "median", "max", "min", "count"):
        grouped = df.groupby(plan.group_by_column)
        series = grouped.size() if plan.operation == "count" else getattr(grouped[plan.value_column], plan.operation)()
        series = series.sort_values(ascending=False)
        value: Any = {str(k): _to_python(v) for k, v in series.items()}
    elif plan.operation == "count":
        value = int(len(df))
    elif plan.operation in ("sum", "mean", "median", "max", "min"):
        value = _to_python(getattr(df[plan.value_column], plan.operation)())
    elif plan.operation in ("top_n", "bottom_n"):
        ascending = plan.operation == "bottom_n"
        ranked = df.sort_values(by=plan.value_column, ascending=ascending).head(plan.n)
        value = ranked.to_dict(orient="records")
    else:  # pragma: no cover -- unreachable given the assert above
        raise ValueError(f"Unsupported operation: {plan.operation}")

    return {
        "operation": plan.operation,
        "value_column": plan.value_column,
        "group_by_column": plan.group_by_column,
        "n": plan.n,
        "value": value,
        "row_count": int(len(df)),
        "file_name": plan.file_name,
    }


_OP_LABELS = {"sum": "Sum", "mean": "Average", "median": "Median", "max": "Maximum", "min": "Minimum"}


def format_result_as_fact(result: Dict[str, Any]) -> str:
    """Render an execute_plan() result as a plain-English statement of fact
    for the LLM to phrase -- every number in here came straight out of
    pandas, computed over the full file."""
    op = result["operation"]
    header = (
        f"Computed directly from all {result['row_count']} rows of "
        f"{result['file_name']} (the full dataset, not a retrieved sample)."
    )

    if result["group_by_column"] and op != "top_n" and op != "bottom_n":
        op_label = "Count" if op == "count" else _OP_LABELS[op]
        subject = "rows" if op == "count" else result["value_column"]
        lines = [header, f"{op_label} of {subject}, grouped by {result['group_by_column']}:"]
        lines.extend(f"  - {k}: {v}" for k, v in result["value"].items())
        return "\n".join(lines)

    if op == "count":
        return f"{header}\nRow count: {result['value']}"

    if op in ("sum", "mean", "median", "max", "min"):
        return f"{header}\n{_OP_LABELS[op]} of {result['value_column']}: {result['value']}"

    # top_n / bottom_n
    label = "Top" if op == "top_n" else "Bottom"
    lines = [header, f"{label} {result['n']} rows ranked by {result['value_column']}:"]
    for i, row in enumerate(result["value"], start=1):
        lines.append(f"  {i}. " + ", ".join(f"{k}={v}" for k, v in row.items()))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Phrasing: hand the LLM the already-computed fact, nothing else
# ---------------------------------------------------------------------------

COMPUTE_PHRASING_PROMPT = PromptTemplate(
    input_variables=["question", "fact"],
    template=(
        "You are ContextIQ, answering a question about the user's uploaded CSV data.\n\n"
        "A fact below has ALREADY been computed exactly, directly from the full dataset "
        "using pandas -- not estimated, not sampled, not retrieved. Your only job is to "
        "phrase this fact as a clear, natural-language answer to the question.\n\n"
        "Rules:\n"
        "- Do NOT recompute, re-derive, round differently, or second-guess any number in "
        "the fact -- treat it as ground truth and report it exactly as given.\n"
        "- Do NOT add any numbers, rows, or claims that are not present in the fact.\n"
        "- Be concise.\n\n"
        "Computed fact:\n{fact}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    ),
)


def _phrase_result(question: str, fact: str) -> str:
    llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL_NAME, temperature=0)
    prompt = COMPUTE_PHRASING_PROMPT.format(question=question, fact=fact)
    response = llm.invoke(prompt)
    return response.content.strip()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def answer_computational_question(
    user_id: int, question: str, file_name: Optional[str] = None
) -> Optional[dict]:
    """Try to answer `question` via exact pandas computation over the user's
    full CSV file, bypassing retrieval entirely.

    Returns a dict shaped like chain.rag_chain.run_rag_chain()'s return value
    ({"answer", "sources", "rewritten_query"}) on success, or None to signal
    "couldn't confidently handle this -- fall back to the normal RAG path."
    """
    target_file = resolve_target_csv_file(user_id, file_name)
    if target_file is None:
        return None

    df = load_csv_dataframe(user_id, target_file)
    if df is None or df.empty:
        return None

    plan = build_compute_plan(question, df, target_file)
    if plan is None:
        return None

    try:
        result = execute_plan(plan, df)
    except Exception:
        logger.exception("csv_compute: failed executing plan %r for %r", plan, target_file)
        return None

    fact = format_result_as_fact(result)

    try:
        answer = _phrase_result(question, fact)
    except Exception:
        logger.exception("csv_compute: LLM phrasing call failed")
        return None

    return {
        "answer": answer,
        "sources": [target_file],
        "rewritten_query": None,
    }
