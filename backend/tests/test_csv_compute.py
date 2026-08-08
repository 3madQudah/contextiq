"""
Tests for the CSV computational query path (chain/csv_compute.py and
chain/csv_query_classifier.py).

The LLM phrasing step (chain.csv_compute._phrase_result) is monkeypatched to
return its input fact verbatim rather than calling the real Groq API -- these
tests are about verifying the *computed number* is correct and that fallback
happens when it should, not about LLM prose, and they should run without
network access or a GROQ_API_KEY.
"""

import os

import pytest

from chain import csv_compute
from chain.csv_query_classifier import is_computational_question


@pytest.fixture
def csv_user(tmp_path, monkeypatch):
    """Point csv_compute at a temp raw-data dir and return a helper to write
    a CSV file into it for a given user id."""
    monkeypatch.setattr(csv_compute, "RAW_DATA_DIR", str(tmp_path))
    # Bypass the real Groq call entirely -- return the computed fact as-is so
    # assertions can check the exact numbers made it through.
    monkeypatch.setattr(csv_compute, "_phrase_result", lambda question, fact: fact)

    def _write(user_id: int, file_name: str, content: str) -> None:
        user_dir = tmp_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        (user_dir / file_name).write_text(content)

    return _write


SALES_CSV = (
    "Region,Product,Revenue\n"
    "APAC,NimbusPro,184203\n"
    "EMEA,NimbusPro,209981\n"
    "NA,NimbusPro,301220\n"
    "APAC,NimbusLite,52310\n"
)


def test_average_aggregation(csv_user):
    csv_user(1, "sales.csv", SALES_CSV)

    result = csv_compute.answer_computational_question(
        user_id=1, question="What is the average revenue?", file_name="sales.csv"
    )

    assert result is not None
    expected_avg = (184203 + 209981 + 301220 + 52310) / 4
    assert str(expected_avg) in result["answer"]
    assert result["sources"] == ["sales.csv"]


def test_top_n_query(csv_user):
    csv_user(1, "sales.csv", SALES_CSV)

    result = csv_compute.answer_computational_question(
        user_id=1, question="What are the top 2 rows by revenue?", file_name="sales.csv"
    )

    assert result is not None
    # Highest two Revenue values, in descending order.
    assert result["answer"].index("301220") < result["answer"].index("209981")
    assert "184203" not in result["answer"]  # 3rd highest, shouldn't be in a top-2


def test_fallback_when_question_is_not_computational(csv_user):
    csv_user(1, "sales.csv", SALES_CSV)
    question = "What does the Region column represent?"

    # The classifier itself shouldn't flag this as computational...
    assert is_computational_question(question) is False

    # ...and even if something upstream calls the compute path anyway, it
    # must decline (return None) rather than guess, so the caller falls back
    # to the normal RAG path.
    result = csv_compute.answer_computational_question(
        user_id=1, question=question, file_name="sales.csv"
    )
    assert result is None


def test_region_named_na_is_not_silently_dropped(csv_user):
    """Regression test: pandas' default NA-sentinel handling turns the
    literal string "NA" (e.g. a "North America" region code) into NaN on
    read, and DataFrame.groupby() drops NaN group keys by default -- so a
    naive pd.read_csv() would silently make the NA region's revenue vanish
    from a group-by total instead of erroring. See load_csv_dataframe()."""
    csv_user(1, "sales.csv", SALES_CSV)  # includes a Region="NA" row (301220)

    result = csv_compute.answer_computational_question(
        user_id=1, question="What is the total revenue by region?", file_name="sales.csv"
    )

    assert result is not None
    assert "NA: 301220" in result["answer"]


def test_fallback_when_multiple_csvs_and_no_file_name(csv_user):
    csv_user(1, "sales.csv", SALES_CSV)
    csv_user(1, "roster.csv", "Name,Salary\nAda,1000\nGrace,2000\n")

    # Ambiguous which file "average revenue" refers to with two CSVs present
    # and no file_name hint -- should fall back rather than guess.
    result = csv_compute.answer_computational_question(
        user_id=1, question="What is the average revenue?", file_name=None
    )
    assert result is None
