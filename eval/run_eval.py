"""
Retrieval evaluation: FAISS-only vs. BM25-only vs. the existing Ensemble
(hybrid) retriever, on eval_set.json.

Read-only with respect to the app: this script does not modify or
reimplement any retrieval/chain logic. It imports and calls the exact same
functions the app itself uses --

  - FAISS-only    : ingestion.vector_store.load_faiss_index(...).as_retriever(...)
  - BM25-only     : ingestion.keyword_store.build_bm25_retriever(...)
  - Ensemble      : chain.hybrid_retriever.get_hybrid_retriever(...)   [unmodified]

The only "new" code here is a small helper that reconstructs a stable
chunk_id (file_name::index) for a retrieved Document by matching it against
the persisted chunks.pkl -- the app itself doesn't store chunk ids, so
there's nothing existing to import for that.

Usage (from eval/):
    python3 run_eval.py
Requires eval fixtures already ingested -- see build_eval_corpus.py.

Writes eval/results.json and eval/results.md.
"""

import json
import math
import os
import statistics
import sys
import time
from datetime import datetime, timezone

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(os.path.dirname(EVAL_DIR), "backend")
sys.path.insert(0, BACKEND_DIR)

from config import EVAL_USER_ID, TOP_K  # noqa: E402

from chain.hybrid_retriever import get_hybrid_retriever  # noqa: E402
from ingestion.keyword_store import build_bm25_retriever, load_chunks  # noqa: E402
from ingestion.vector_store import load_faiss_index  # noqa: E402

EVAL_SET_PATH = os.path.join(EVAL_DIR, "eval_set.json")
RESULTS_JSON_PATH = os.path.join(EVAL_DIR, "results.json")
RESULTS_MD_PATH = os.path.join(EVAL_DIR, "results.md")

NUM_WARMUP_CALLS = 1  # discarded, before timing starts (avoids counting one-time model load)


# ---------------------------------------------------------------------------
# chunk_id resolution -- the smallest possible helper, not a new library.
# The app never persists a chunk id, so we reconstruct the same one
# build_eval_corpus.py implicitly assigned: position within a file's chunk
# list, in persisted (= ingestion) order.
# ---------------------------------------------------------------------------

def build_chunk_id_map(user_id):
    """Return {(file_name, page_content): 'file_name::index'} from the
    persisted chunks for this user (read-only; reuses load_chunks)."""
    chunks = load_chunks(user_id) or []
    id_map = {}
    counters = {}
    for chunk in chunks:
        file_name = chunk.metadata.get("file_name")
        idx = counters.get(file_name, 0)
        counters[file_name] = idx + 1
        id_map[(file_name, chunk.page_content)] = f"{file_name}::{idx}"
    return id_map


def resolve_chunk_id(doc, id_map):
    key = (doc.metadata.get("file_name"), doc.page_content)
    return id_map.get(key, f"UNRESOLVED::{key[0]}")


# ---------------------------------------------------------------------------
# Retriever configs. Each builder is called fresh per query (no caching),
# matching how chain/hybrid_retriever.py and chain/rag_chain.py actually
# behave today -- get_hybrid_retriever() reloads FAISS from disk and rebuilds
# BM25 from chunks.pkl on every call. So "latency" below is genuine
# per-request latency as currently implemented, not just raw ANN search time.
# ---------------------------------------------------------------------------

def build_faiss_only(user_id, k):
    store = load_faiss_index(user_id)
    if store is None:
        return None
    return store.as_retriever(search_kwargs={"k": k})


def build_bm25_only(user_id, k):
    retriever = build_bm25_retriever(user_id)
    if retriever is None:
        return None
    retriever.k = k
    return retriever


def build_ensemble(user_id, k):
    # get_hybrid_retriever is unmodified app code; k is unused (it hardcodes
    # TOP_K_PER_RETRIEVER=8 per sub-retriever internally) but kept in the
    # signature so all three builders share one call shape below.
    return get_hybrid_retriever(user_id)


CONFIGS = [
    ("FAISS-only", build_faiss_only),
    ("BM25-only", build_bm25_only),
    ("Ensemble (Hybrid)", build_ensemble),
]


# ---------------------------------------------------------------------------
# Metrics (standard IR definitions, K fixed at TOP_K)
# ---------------------------------------------------------------------------

def precision_at_k(retrieved_ids, relevant_ids, k):
    topk = retrieved_ids[:k]
    if not topk:
        return 0.0
    hits = sum(1 for c in topk if c in relevant_ids)
    return hits / k


def recall_at_k(retrieved_ids, relevant_ids, k):
    if not relevant_ids:
        return 0.0
    topk = set(retrieved_ids[:k])
    hits = len(topk & relevant_ids)
    return hits / len(relevant_ids)


def reciprocal_rank(retrieved_ids, relevant_ids, k):
    for rank, c in enumerate(retrieved_ids[:k], start=1):
        if c in relevant_ids:
            return 1.0 / rank
    return 0.0


def average_precision(retrieved_ids, relevant_ids, k):
    if not relevant_ids:
        return 0.0
    topk = retrieved_ids[:k]
    hits = 0
    precisions = []
    for rank, c in enumerate(topk, start=1):
        if c in relevant_ids:
            hits += 1
            precisions.append(hits / rank)
    denom = min(len(relevant_ids), k)
    return sum(precisions) / denom if precisions else 0.0


def percentile(values, pct):
    """Linear-interpolation percentile (standard 'inclusive' method)."""
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    rank = (len(s) - 1) * (pct / 100)
    lo, hi = math.floor(rank), math.ceil(rank)
    if lo == hi:
        return s[int(rank)]
    return s[lo] + (s[hi] - s[lo]) * (rank - lo)


# ---------------------------------------------------------------------------
# Main eval loop
# ---------------------------------------------------------------------------

def run_config(name, build_fn, questions, id_map):
    per_question = []

    # Warm-up: absorbs first-call costs (e.g. embedding model weight load)
    # that are process-startup artifacts, not steady-state per-query latency.
    for _ in range(NUM_WARMUP_CALLS):
        warm_retriever = build_fn(EVAL_USER_ID, TOP_K)
        if warm_retriever is not None:
            warm_retriever.invoke(questions[0]["question"])

    for q in questions:
        relevant_ids = set(q["relevant_chunk_ids"])

        t0 = time.perf_counter()
        retriever = build_fn(EVAL_USER_ID, TOP_K)
        docs = retriever.invoke(q["question"]) if retriever is not None else []
        latency_ms = (time.perf_counter() - t0) * 1000

        docs = docs[:TOP_K]
        retrieved_ids = [resolve_chunk_id(d, id_map) for d in docs]

        per_question.append(
            {
                "id": q["id"],
                "question": q["question"],
                "file_type": q["file_type"],
                "category": q.get("category", "general"),
                "relevant_chunk_ids": sorted(relevant_ids),
                "retrieved_chunk_ids": retrieved_ids,
                "precision_at_k": precision_at_k(retrieved_ids, relevant_ids, TOP_K),
                "recall_at_k": recall_at_k(retrieved_ids, relevant_ids, TOP_K),
                "reciprocal_rank": reciprocal_rank(retrieved_ids, relevant_ids, TOP_K),
                "average_precision": average_precision(retrieved_ids, relevant_ids, TOP_K),
                "latency_ms": latency_ms,
            }
        )

    latencies = [pq["latency_ms"] for pq in per_question]

    def mean_of(field):
        return sum(pq[field] for pq in per_question) / len(per_question)

    def mean_of_subset(field, category):
        subset = [pq[field] for pq in per_question if pq["category"] == category]
        return sum(subset) / len(subset) if subset else None

    aggregate = {
        "precision_at_k": mean_of("precision_at_k"),
        "recall_at_k": mean_of("recall_at_k"),
        "mrr": mean_of("reciprocal_rank"),
        "map": mean_of("average_precision"),
        "latency_ms": {
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
            "mean": statistics.mean(latencies),
        },
        "recall_at_k_by_category": {
            category: mean_of_subset("recall_at_k", category)
            for category in sorted({pq["category"] for pq in per_question})
        },
    }

    return {"per_question": per_question, "aggregate": aggregate}


def main():
    with open(EVAL_SET_PATH) as f:
        eval_set = json.load(f)
    questions = eval_set["questions"]

    id_map = build_chunk_id_map(EVAL_USER_ID)
    if not id_map:
        print(
            f"No persisted chunks found for eval user_id={EVAL_USER_ID}. "
            "Run build_eval_corpus.py first.",
            file=sys.stderr,
        )
        sys.exit(1)

    results = {"configs": {}}
    for name, build_fn in CONFIGS:
        print(f"Running {name}...")
        results["configs"][name] = run_config(name, build_fn, questions, id_map)

    results["meta"] = {
        "eval_user_id": EVAL_USER_ID,
        "top_k": TOP_K,
        "num_questions": len(questions),
        "num_indexed_chunks": len(id_map),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology_notes": [
            "Latency includes retriever construction (FAISS load from disk / "
            "BM25Retriever rebuild from chunks.pkl / get_hybrid_retriever) plus "
            "the retrieval call itself, because that is the actual per-request "
            "cost today -- chain/hybrid_retriever.py builds both indexes fresh "
            "on every call, with no cross-request caching.",
            "One untimed warm-up call precedes each config's timed loop to "
            "absorb one-time process costs (e.g. first embedding-model load).",
            "Ensemble (Hybrid) uses the unmodified chain.hybrid_retriever."
            "get_hybrid_retriever(), which pulls top-8 from each of FAISS and "
            "BM25 before RRF-fusing; results here are that fused list's top-K.",
        ],
    }

    with open(RESULTS_JSON_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote {RESULTS_JSON_PATH}")

    write_markdown_report(results, questions)
    print(f"Wrote {RESULTS_MD_PATH}")


def write_markdown_report(results, questions):
    configs = results["configs"]
    meta = results["meta"]
    names = [name for name, _ in CONFIGS]

    lines = []
    lines.append("# ContextIQ Retrieval Evaluation")
    lines.append("")
    lines.append(
        f"Generated {meta['generated_at']} · {meta['num_questions']} questions · "
        f"{meta['num_indexed_chunks']} indexed chunks · K={meta['top_k']} · "
        f"eval user_id={meta['eval_user_id']}"
    )
    lines.append("")
    lines.append(
        "> **Before citing these numbers:** see `eval_set.json`'s `_meta.READ_ME_BEFORE_CITING`. "
        "This corpus is a small (17-chunk, 10-document) synthetic fixture built to guarantee "
        "coverage of all 5 file types, because the dev environment had almost no real indexed "
        "data. Treat results as a controlled illustration of hybrid-vs-single-retriever "
        "behavior, not a production-scale benchmark."
    )
    lines.append("")

    # --- Summary table ---
    lines.append("## Summary (averaged over all questions)")
    lines.append("")
    header = "| Metric | " + " | ".join(names) + " |"
    sep = "|---|" + "|".join(["---"] * len(names)) + "|"
    lines.append(header)
    lines.append(sep)

    def fmt(v, pct=False, dp=3):
        if v is None:
            return "n/a"
        return f"{v*100:.1f}%" if pct else f"{v:.{dp}f}"

    rows = [
        ("Precision@K", lambda c: fmt(c["aggregate"]["precision_at_k"], pct=True)),
        ("Recall@K", lambda c: fmt(c["aggregate"]["recall_at_k"], pct=True)),
        ("MRR", lambda c: fmt(c["aggregate"]["mrr"])),
        ("MAP", lambda c: fmt(c["aggregate"]["map"])),
        ("Latency p50 (ms)", lambda c: fmt(c["aggregate"]["latency_ms"]["p50"], dp=1)),
        ("Latency p95 (ms)", lambda c: fmt(c["aggregate"]["latency_ms"]["p95"], dp=1)),
    ]
    for label, getter in rows:
        lines.append(f"| {label} | " + " | ".join(getter(configs[n]) for n in names) + " |")
    lines.append("")

    # --- Category breakdown ---
    lines.append("## Recall@K by question category")
    lines.append("")
    categories = sorted(
        {pq["category"] for pq in configs[names[0]]["per_question"]}
    )
    lines.append("| Category | " + " | ".join(names) + " |")
    lines.append("|---|" + "|".join(["---"] * len(names)) + "|")
    for cat in categories:
        row = [
            fmt(configs[n]["aggregate"]["recall_at_k_by_category"].get(cat), pct=True)
            for n in names
        ]
        lines.append(f"| {cat} | " + " | ".join(row) + " |")
    lines.append("")

    # --- Takeaways (data-derived, not hardcoded) ---
    lines.append("## Takeaways")
    lines.append("")

    faiss_recall = configs["FAISS-only"]["aggregate"]["recall_at_k"]
    bm25_recall = configs["BM25-only"]["aggregate"]["recall_at_k"]
    hybrid_recall = configs["Ensemble (Hybrid)"]["aggregate"]["recall_at_k"]

    def pct_delta(new, old):
        if old == 0:
            return "n/a (baseline was 0)"
        return f"{(new - old) / old * 100:+.1f}%"

    lines.append(
        f"- **Hybrid vs. FAISS-only:** Recall@{meta['top_k']} went from "
        f"{faiss_recall*100:.1f}% (FAISS-only) to {hybrid_recall*100:.1f}% (Hybrid), "
        f"a {pct_delta(hybrid_recall, faiss_recall)} relative change."
    )
    lines.append(
        f"- **Hybrid vs. BM25-only:** Recall@{meta['top_k']} went from "
        f"{bm25_recall*100:.1f}% (BM25-only) to {hybrid_recall*100:.1f}% (Hybrid), "
        f"a {pct_delta(hybrid_recall, bm25_recall)} relative change."
    )

    rare_term_faiss = configs["FAISS-only"]["aggregate"]["recall_at_k_by_category"].get(
        "rare_term"
    )
    rare_term_hybrid = configs["Ensemble (Hybrid)"]["aggregate"][
        "recall_at_k_by_category"
    ].get("rare_term")
    if rare_term_faiss is not None and rare_term_hybrid is not None:
        lines.append(
            f"- **On exact-number/rare-term questions specifically** (the case hybrid "
            f"retrieval exists for): FAISS-only Recall@{meta['top_k']} was "
            f"{rare_term_faiss*100:.1f}% vs. Hybrid's {rare_term_hybrid*100:.1f}% "
            f"({pct_delta(rare_term_hybrid, rare_term_faiss)} relative)."
        )

    faiss_p50 = configs["FAISS-only"]["aggregate"]["latency_ms"]["p50"]
    bm25_p50 = configs["BM25-only"]["aggregate"]["latency_ms"]["p50"]
    hybrid_p50 = configs["Ensemble (Hybrid)"]["aggregate"]["latency_ms"]["p50"]
    lines.append(
        f"- **Latency:** median per-query latency was {faiss_p50:.1f}ms (FAISS-only), "
        f"{bm25_p50:.1f}ms (BM25-only), {hybrid_p50:.1f}ms (Hybrid) -- Hybrid pays for "
        "querying both indexes and fusing results, on top of neither index being cached "
        "between requests today (see methodology notes in results.json)."
    )
    lines.append("")

    # --- Per-question detail ---
    lines.append("## Per-question detail")
    lines.append("")
    lines.append(
        "| ID | Question | Type | Category | " + " | ".join(f"{n} Recall@K" for n in names) + " |"
    )
    lines.append("|---|---|---|---|" + "|".join(["---"] * len(names)) + "|")
    for q in questions:
        qid = q["id"]
        pq_by_config = {
            n: next(pq for pq in configs[n]["per_question"] if pq["id"] == qid)
            for n in names
        }
        recalls = [
            "✅" if pq_by_config[n]["recall_at_k"] == 1.0 else "❌" for n in names
        ]
        question_text = q["question"].replace("|", "\\|")
        lines.append(
            f"| {qid} | {question_text} | {q['file_type']} | {q.get('category','general')} | "
            + " | ".join(recalls)
            + " |"
        )
    lines.append("")
    lines.append(
        "`✅` = the correct chunk was found somewhere in the top-K; `❌` = it wasn't. "
        "Full ranked retrieved-chunk-ids and raw metric values per question are in `results.json`."
    )
    lines.append("")

    with open(RESULTS_MD_PATH, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
