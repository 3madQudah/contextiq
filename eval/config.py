"""Shared constants for the eval scripts."""

# Dedicated user id for the synthetic eval corpus (see build_eval_corpus.py).
# Does not correspond to a real auth DB user -- ingestion only keys off this
# id for on-disk path partitioning (data/raw/<id>, data/vector_index/<id>),
# so no DB row is required.
EVAL_USER_ID = 9001

TOP_K = 4
