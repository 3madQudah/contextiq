import { MessageSquarePlus } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import Composer from "../components/Composer.jsx";
import MessageBubble from "../components/MessageBubble.jsx";
import TypingIndicator from "../components/TypingIndicator.jsx";
import { useAppData } from "../context/AppDataContext.jsx";
import { getExtension } from "../lib/fileTypes.js";
import { generateTitle } from "../lib/titles.js";
import { askQuestion, getConversation, getErrorMessage, renameConversation } from "../services/api.js";

const EXAMPLE_QUESTIONS = [
  "What are the key points across my documents?",
  "Summarize the file I uploaded most recently.",
  "Are there any numbers or dates I should know about?",
];

export default function Chat() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { refreshConversations } = useAppData();

  const [messages, setMessages] = useState([]);
  const [conversationLoading, setConversationLoading] = useState(false);
  const [conversationError, setConversationError] = useState("");
  const [sending, setSending] = useState(false);
  const [activeFilter, setActiveFilter] = useState(null);

  const scrollRef = useRef(null);
  const skipNextFetchRef = useRef(false);

  useEffect(() => {
    if (skipNextFetchRef.current) {
      // We navigated here ourselves right after sending the first message of
      // a new conversation (see handleSend) — messages and the active filter
      // are already correct, so skip re-fetching and don't reset the filter.
      skipNextFetchRef.current = false;
      return;
    }

    setActiveFilter(null);

    if (!conversationId) {
      setMessages([]);
      setConversationError("");
      return;
    }

    let ignore = false;
    setConversationLoading(true);
    setConversationError("");

    getConversation(conversationId)
      .then((data) => {
        if (ignore) return;
        setMessages(
          data.messages.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            sources: m.sources || [],
            // rewritten_query isn't persisted on the Message model server-side
            // (it only comes back on the live /chat/ask response), so it's
            // never available when restoring history — only for messages
            // sent in this session, appended below in handleSend.
            rewrittenQuery: null,
          }))
        );
      })
      .catch((err) => {
        if (!ignore) setConversationError(getErrorMessage(err, "Couldn't load this conversation."));
      })
      .finally(() => {
        if (!ignore) setConversationLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [conversationId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  async function handleSend(question) {
    const isNewConversation = !conversationId;
    const userMessage = { id: `local-user-${Date.now()}`, role: "user", content: question, sources: [] };
    setMessages((prev) => [...prev, userMessage]);
    setSending(true);

    try {
      const data = await askQuestion({
        question,
        conversation_id: conversationId ? Number(conversationId) : null,
        file_type: activeFilter,
      });

      const showRewrite = data.rewritten_query && data.rewritten_query !== question;
      const assistantMessage = {
        id: `local-assistant-${Date.now()}`,
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
        rewrittenQuery: showRewrite ? data.rewritten_query : null,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (isNewConversation) {
        skipNextFetchRef.current = true;
        navigate(`/app/chat/${data.conversation_id}`, { replace: true });
        renameConversation(data.conversation_id, generateTitle(question))
          .then(() => refreshConversations())
          .catch(() => {});
      }
      refreshConversations();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `local-error-${Date.now()}`,
          role: "assistant",
          error: true,
          content: getErrorMessage(err, "Failed to generate an answer. Please try again."),
        },
      ]);
      // If this was the first message of a brand-new chat, the backend still
      // created the conversation and persisted the user's message before the
      // LLM call failed (see backend api/chat_routes.py) — but its id never
      // reaches us, since the error response doesn't carry one. We can't
      // resume it inline without that id, but refreshing at least surfaces it
      // in the sidebar so the user can click into it and continue from there.
      if (isNewConversation) refreshConversations();
    } finally {
      setSending(false);
    }
  }

  function handleSourceClick(sourceFilename) {
    setActiveFilter(getExtension(sourceFilename));
  }

  const showEmptyState = !conversationId && messages.length === 0 && !sending;

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">
        <div className="mx-auto flex max-w-2xl flex-col gap-5">
          {conversationLoading && <p className="text-sm text-muted">Loading conversation…</p>}
          {conversationError && <p className="text-sm text-danger">{conversationError}</p>}

          {showEmptyState && (
            <div className="flex flex-col items-center gap-4 py-16 text-center">
              <MessageSquarePlus size={22} strokeWidth={1.5} className="text-muted" />
              <div>
                <h2 className="text-base font-medium text-foreground">Start a new conversation</h2>
                <p className="mt-1 text-sm text-muted">Ask anything about your uploaded documents.</p>
              </div>
              <div className="flex flex-col gap-2">
                {EXAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="rounded-md border border-border px-3.5 py-2 text-sm text-foreground transition-colors hover:bg-surface-hover"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} onSourceClick={handleSourceClick} />
          ))}

          {sending && <TypingIndicator />}
        </div>
      </div>

      <Composer
        onSend={handleSend}
        disabled={sending}
        activeFilter={activeFilter}
        onClearFilter={() => setActiveFilter(null)}
      />
    </div>
  );
}
