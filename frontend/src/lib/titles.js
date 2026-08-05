const STOPWORDS = new Set([
  "what", "whats", "is", "are", "the", "a", "an", "of", "in", "on", "for", "about",
  "to", "and", "or", "do", "does", "can", "could", "would", "will", "you", "your",
  "my", "me", "please", "tell", "explain", "how", "why", "when", "where", "who",
  "which", "this", "that", "these", "those", "with", "from", "i", "it", "its", "was",
]);

// Client-side heuristic title generator. The "correct" version of this — ask
// an LLM for a real 3-5 word summary — needs either a backend change (a new
// endpoint, since GROQ_API_KEY only exists server-side) or exposing that key
// in the browser, and neither is something to do without asking first. This
// is a keyword-extraction approximation in the meantime: strip punctuation,
// drop stopwords, take the first few remaining words. Good enough to beat
// "showing the raw truncated question," not a substitute for real summarization.
export function generateTitle(question) {
  const words = question.replace(/[?!.,;:]/g, "").split(/\s+/).filter(Boolean);
  const meaningful = words.filter((w) => !STOPWORDS.has(w.toLowerCase()));
  const chosen = (meaningful.length >= 3 ? meaningful : words).slice(0, 5);
  const title = chosen.join(" ");
  return title.length > 48 ? title.slice(0, 48).trim() : title || question.slice(0, 48);
}
