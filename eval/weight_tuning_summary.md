# FAISS/BM25 Weight Tuning Summary

All 4 runs use the same `eval_set.json` (28 questions, 17-chunk synthetic corpus,
eval user_id=9001), K=4 (matching `rag_chain.py`'s real `TOP_K`), against the
**Ensemble (Hybrid)** retriever only — FAISS-only and BM25-only are unaffected
by these weights and are omitted here (see the individual `results_*.md` files
for their unchanged numbers).

| Weights (FAISS / BM25) | Precision@4 | Recall@4 | MRR | MAP | Latency p50 (ms) | Latency p95 (ms) | Results file |
|---|---|---|---|---|---|---|---|
| 0.5 / 0.5 (current default) | 25.0% | 100.0% | 0.893 | 0.893 | 12.4 | 13.6 | `results_baseline_k4.md` |
| 0.6 / 0.4 | 25.0% | 100.0% | 0.899 | 0.899 | 12.6 | 16.2 | `results_weights_0.6_0.4.md` |
| 0.7 / 0.3 | 25.0% | 100.0% | 0.899 | 0.899 | 13.0 | 17.3 | `results_weights_0.7_0.3.md` |
| 0.8 / 0.2 | 25.0% | 100.0% | 0.899 | 0.899 | 12.6 | 13.7 | `results_weights_0.8_0.2.md` |

## What actually moved

Precision@4 and Recall@4 are **identical across all four weightings** — every
alternative retrieves the same set of correct chunks within top-4 as the
baseline, just occasionally in a different order.

MRR/MAP move by a single, identical step (+0.006 absolute, +0.67% relative)
the moment FAISS weight reaches 0.6, and **do not move any further** at 0.7 or
0.8. Tracing it through `results.json`: exactly one question out of 28 changes
rank —

- **q04** ("Which CVE was fixed in Nimbus Sync version 3.4.2?"): the correct
  chunk (`security_audit_report.pdf::0`) moves from rank 3 to rank 2 in the
  fused list once FAISS is weighted ≥0.6. No other question's ranking changes
  at any tested weight combination.

Latency differences across weightings (12.4–17.3ms) show no consistent trend
with weight and are within the run-to-run noise already documented in the
baseline report (index rebuild on every call, no caching) — not a real effect
of the weight value itself.

## Recommendation

**No alternative clearly beats 0.5/0.5 — I would not adopt a new default from
this data.** The only measurable change (MRR/MAP +0.67%) is driven by a single
question out of 28 re-ranking from position 3 to position 2; precision and
recall are unchanged everywhere. On a 17-chunk corpus, a one-question effect
is well within what could flip either direction on a different but equally
plausible question set — it's not evidence of a generalizable improvement,
just a data point.

If you do want to move off 0.5/0.5 anyway (e.g. because the direction is at
least never negative here), 0.6/0.4 captures the entire observed benefit with
the smallest deviation from the current balanced design — 0.7/0.3 and 0.8/0.2
buy nothing further. But per your instruction, since nothing here *clearly*
beats the baseline, the honest recommendation is: **keep 0.5/0.5**, and revisit
this once the eval corpus is larger — a 17-chunk set can't distinguish a real
weighting effect from single-question noise.

`backend/chain/hybrid_retriever.py` has been left at `FAISS_WEIGHT = 0.5`,
`BM25_WEIGHT = 0.5` (verified via `git diff` — no net change), per your
instructions.
