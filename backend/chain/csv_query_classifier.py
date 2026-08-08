"""
Lightweight keyword/pattern classifier that flags whether a question asked
against a CSV-typed request is likely asking for a computed aggregate (sum,
average, count, min/max, top-N, group-by) rather than a descriptive/
exploratory lookup.

Deliberately regex-based, not an LLM call: a false positive here just means
chain/csv_compute.py attempts to build a compute plan and safely falls back
to the normal RAG path when it can't confidently resolve one (see
build_compute_plan there) -- so a cheap, explainable, zero-latency heuristic
is preferable to a slower, costlier model call for this gate. A false
negative just means a computable question goes through RAG as it does today,
which is the pre-existing behavior this feature is layered on top of, so it's
not a regression either way.
"""

import re

_COMPUTE_PATTERNS = (
    r"\b(average|mean|median)\b",
    r"\b(total|sum)\b",
    r"\b(count|how many|number of)\b",
    r"\btop\s+\d+\b",
    r"\bbottom\s+\d+\b",
    r"\b(highest|largest|greatest|maximum|max)\b",
    r"\b(lowest|smallest|least|minimum|min)\b",
    r"\b(group(ed)?\s+by)\b",
)

_COMPUTE_RE = re.compile("|".join(_COMPUTE_PATTERNS), re.IGNORECASE)


def is_computational_question(question: str) -> bool:
    """True if `question` contains language suggesting it wants a computed
    aggregate over CSV data (e.g. "what's the average X", "top 5 by Y",
    "how many rows have Z") rather than a descriptive lookup."""
    return bool(_COMPUTE_RE.search(question))
