# ContextIQ Retrieval Evaluation

Generated 2026-08-07T14:39:29.690203+00:00 · 28 questions · 17 indexed chunks · K=4 · eval user_id=9001

> **Before citing these numbers:** see `eval_set.json`'s `_meta.READ_ME_BEFORE_CITING`. This corpus is a small (17-chunk, 10-document) synthetic fixture built to guarantee coverage of all 5 file types, because the dev environment had almost no real indexed data. Treat results as a controlled illustration of hybrid-vs-single-retriever behavior, not a production-scale benchmark.

## Summary (averaged over all questions)

| Metric | FAISS-only | BM25-only | Ensemble (Hybrid) |
|---|---|---|---|
| Precision@K | 25.0% | 22.3% | 25.0% |
| Recall@K | 100.0% | 89.3% | 100.0% |
| MRR | 0.964 | 0.869 | 0.893 |
| MAP | 0.964 | 0.869 | 0.893 |
| Latency p50 (ms) | 12.2 | 0.7 | 12.4 |
| Latency p95 (ms) | 44.6 | 0.8 | 13.6 |

## Recall@K by question category

| Category | FAISS-only | BM25-only | Ensemble (Hybrid) |
|---|---|---|---|
| exact_number | 100.0% | 87.5% | 100.0% |
| rare_term | 100.0% | 91.7% | 100.0% |

## Takeaways

- **Hybrid vs. FAISS-only:** Recall@4 went from 100.0% (FAISS-only) to 100.0% (Hybrid), a +0.0% relative change.
- **Hybrid vs. BM25-only:** Recall@4 went from 89.3% (BM25-only) to 100.0% (Hybrid), a +12.0% relative change.
- **On exact-number/rare-term questions specifically** (the case hybrid retrieval exists for): FAISS-only Recall@4 was 100.0% vs. Hybrid's 100.0% (+0.0% relative).
- **Latency:** median per-query latency was 12.2ms (FAISS-only), 0.7ms (BM25-only), 12.4ms (Hybrid) -- Hybrid pays for querying both indexes and fusing results, on top of neither index being cached between requests today (see methodology notes in results.json).

## Per-question detail

| ID | Question | Type | Category | FAISS-only Recall@K | BM25-only Recall@K | Ensemble (Hybrid) Recall@K |
|---|---|---|---|---|---|---|
| q01 | What uptime SLA does Nimbus Sync guarantee? | txt | exact_number | ✅ | ✅ | ✅ |
| q02 | What conflict resolution technique does Nimbus Sync use to merge concurrent edits from multiple devices? | txt | rare_term | ✅ | ✅ | ✅ |
| q03 | How much does the Nimbus Sync Pro plan cost per month? | txt | exact_number | ✅ | ✅ | ✅ |
| q04 | Which CVE was fixed in Nimbus Sync version 3.4.2? | txt | rare_term | ✅ | ❌ | ✅ |
| q05 | By what percentage did sync latency improve in version 3.4.2? | txt | exact_number | ✅ | ✅ | ✅ |
| q06 | What was the maximum number of linked devices per account before it was increased in version 3.4.1? | txt | exact_number | ✅ | ✅ | ✅ |
| q07 | What --max-replicas value is recommended for the sync-worker autoscaler? | md | exact_number | ✅ | ✅ | ✅ |
| q08 | What tool is used for canary rollouts of Nimbus Sync in production? | md | rare_term | ✅ | ✅ | ✅ |
| q09 | What Helm chart version is currently pinned for the Kubernetes deployment? | md | exact_number | ✅ | ✅ | ✅ |
| q10 | What is the Nimbus Sync API's rate limit per API key? | md | exact_number | ✅ | ✅ | ✅ |
| q11 | What error code is returned when the Nimbus Sync API rate limit is exceeded? | md | rare_term | ✅ | ✅ | ✅ |
| q12 | How long are Nimbus Sync API bearer tokens valid before they expire? | md | exact_number | ✅ | ✅ | ✅ |
| q13 | What was the NA region's Q3 revenue for NimbusPro? | csv | exact_number | ✅ | ✅ | ✅ |
| q14 | What was APAC's Q1 revenue for NimbusLite? | csv | exact_number | ✅ | ❌ | ✅ |
| q15 | What was EMEA's Q4 revenue for NimbusPro? | csv | exact_number | ✅ | ❌ | ✅ |
| q16 | What department does Fatima Al-Sayed work in? | csv | rare_term | ✅ | ✅ | ✅ |
| q17 | What is Tomasz Wozniak's salary? | csv | rare_term | ✅ | ✅ | ✅ |
| q18 | When was Priya Chandrasekaran hired? | csv | rare_term | ✅ | ✅ | ✅ |
| q19 | What budget did the board approve for the Nimbus Sync infrastructure expansion? | pdf | exact_number | ✅ | ✅ | ✅ |
| q20 | How many of the board's 9 members were present at the 2025-10-14 meeting, and what clause did that invoke? | pdf | rare_term | ✅ | ✅ | ✅ |
| q21 | How many critical severity findings did the security audit identify? | pdf | exact_number | ✅ | ✅ | ✅ |
| q22 | What kind of race condition was found in the file-locking subsystem? | pdf | rare_term | ✅ | ✅ | ✅ |
| q23 | Which CVE does critical finding NS-2025-02 correspond to? | pdf | rare_term | ✅ | ✅ | ✅ |
| q24 | Within how many days does the security audit recommend remediating critical and high findings? | pdf | exact_number | ✅ | ✅ | ✅ |
| q25 | What form must an employee file if they work remotely for more than 14 consecutive days? | docx | rare_term | ✅ | ✅ | ✅ |
| q26 | At what rate does paid time off accrue per month for full-time employees? | docx | exact_number | ✅ | ✅ | ✅ |
| q27 | What onboarding protocol pairs new hires with an existing team member? | docx | rare_term | ✅ | ✅ | ✅ |
| q28 | Within how many business days must IT provisioning be completed after offer acceptance? | docx | exact_number | ✅ | ✅ | ✅ |

`✅` = the correct chunk was found somewhere in the top-K; `❌` = it wasn't. Full ranked retrieved-chunk-ids and raw metric values per question are in `results.json`.
