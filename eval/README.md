# Retrieval eval

Compares FAISS-only, BM25-only, and the existing Ensemble (hybrid) retriever
from `chain/hybrid_retriever.py` on Precision@5, Recall@5, MRR, MAP, and
latency (p50/p95). Read-only w.r.t. app logic -- it only imports and calls
existing retriever/ingestion functions.

## Why there's a `fixtures/` folder

The dev environment had almost no indexed data (6 chunks, no pdf/docx) when
this was built, so a small synthetic 10-document corpus covering all 5 file
types was written to `fixtures/` and ingested into a dedicated eval user
(`user_id=9001`, see `config.py`) via the app's own unmodified ingestion
pipeline. **See `eval_set.json`'s `_meta.READ_ME_BEFORE_CITING` before citing
any numbers publicly** -- it explains what this does and doesn't demonstrate.

Your real users' data (`data/raw/1`, `data/raw/3`, etc.) is untouched.

## Files

- `fixtures/` -- the 10 synthetic source documents (2 per file type). `fixtures/source/` holds
  the plaintext originals for the 4 docs that needed converting to real
  `.pdf`/`.docx` binaries (via macOS `cupsfilter` and `python-docx`, no new
  dependencies) -- kept for transparency, not read by any script.
- `build_eval_corpus.py` -- one-time script that ingests `fixtures/` into
  eval user 9001. Re-run any time to rebuild that user's index from scratch.
- `eval_set.json` -- 28 questions with ground-truth `relevant_chunk_ids`.
- `run_eval.py` -- runs all 3 retriever configs against `eval_set.json`,
  writes `results.json` (raw numbers) and `results.md` (summary report).
- `config.py` -- `EVAL_USER_ID` / `TOP_K` shared by both scripts.

## Reproducing

```bash
cd eval
python3 build_eval_corpus.py   # only needed once, or after editing fixtures/
python3 run_eval.py
```

## Known issue found along the way (unrelated to this eval, pre-existing)

`loaders/document_loader.py` maps `.docx` to `Docx2txtLoader`, which needs
the `docx2txt` package -- it wasn't installed, so **DOCX uploads were broken
in the app itself**, not just in this eval. Installed it locally to unblock
the eval corpus build; add `docx2txt` to `backend/requirements.txt` to fix
it for real.
