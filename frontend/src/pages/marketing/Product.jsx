import { motion } from "motion/react";

import PublicFooter from "../../components/landing/PublicFooter.jsx";
import PublicNav from "../../components/landing/PublicNav.jsx";
import StepList from "../../components/landing/StepList.jsx";
import { easeOut } from "../../lib/motion.js";

// Copy verified against the actual pipeline code before publishing:
//   1. ingestion/chunking.py — chunk_size=1000, chunk_overlap=150;
//      loaders/document_loader.py — section_heading metadata for DOCX/MD.
//   2. ingestion/vector_store.py + ingestion/keyword_store.py — per-user
//      FAISS dir and BM25-backing chunks.pkl, both keyed by user_id.
//   3. chain/query_rewriter.py — rewrite_query() runs before retrieval,
//      only when there's conversation history (i.e. on follow-ups); the
//      ORIGINAL question is still what gets answered.
//   4. chain/hybrid_retriever.py — FAISS_WEIGHT=BM25_WEIGHT=0.5 (equal);
//      chain/rag_chain.py — FETCH_K=8, TOP_K=4, file-type-tailored prompt
//      when every retrieved chunk agrees on one type; prompt_eng/base_prompt.py
//      instructs the model to answer "using ONLY the context below".
//   5. chain/rag_chain.py — sources = sorted(set(...)), rendered as chips
//      by MessageBubble/SourceChip in the chat UI.
// All five checked out — no discrepancies found.
const STEPS = [
  {
    title: "Upload and chunking",
    body: "Each file type — PDF, DOCX, TXT, CSV, or Markdown — goes through its own loader. Text is split into 1000-character chunks with 150 characters of overlap between them, so context isn't lost at chunk boundaries. For DOCX and Markdown files specifically, section headings are preserved as metadata on each chunk.",
  },
  {
    title: "Hybrid indexing",
    body: "Every chunk is added to two separate indexes scoped to your account alone: a FAISS index for semantic (vector similarity) search, and a BM25 index for exact keyword search. Both live in a directory keyed to your user ID — no other account's documents are ever part of your search space.",
  },
  {
    title: "Query rewriting",
    body: "When you ask a follow-up in an existing conversation, it's first rewritten into a standalone question using recent conversation history — resolving pronouns like “it” or “the second one” into what they actually refer to — before that rewritten version is used for retrieval.",
    note: "The original question, not the rewritten one, is still what gets answered — replies read naturally rather than echoing the rewrite.",
  },
  {
    title: "Retrieval and answering",
    body: "An EnsembleRetriever merges results from the FAISS and BM25 indexes with equal weighting, pulling 8 candidates from each before narrowing to the 4 most relevant chunks. Those chunks go to the model inside a prompt — tailored to the file type when every retrieved chunk agrees on one — that instructs it to answer strictly from that context and say so when the context isn't enough.",
  },
  {
    title: "Citation",
    body: "The file name behind every chunk used in the answer is collected into a deduplicated, alphabetically sorted list and returned alongside it. The chat UI renders each one as a clickable source chip beneath the response.",
  },
];

export default function Product() {
  return (
    <div className="min-h-screen bg-bg">
      <PublicNav active="product" />

      <main className="mx-auto max-w-3xl px-6 py-16 sm:py-20">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: easeOut }}
          className="text-center"
        >
          <h1 className="mt-2 text-display-xs font-medium leading-tight text-foreground">
            The RAG pipeline, step by step.
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-md text-muted">
            From the moment a file is uploaded to the moment an answer with citations comes
            back — this is exactly what ContextIQ does in between, with nothing glossed over.
          </p>
        </motion.div>

        <div className="mt-12">
          <StepList steps={STEPS} />
        </div>
      </main>

      <PublicFooter />
    </div>
  );
}
