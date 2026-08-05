import { motion } from "framer-motion";

import Markdown from "./Markdown.jsx";
import SourceChip from "./SourceChip.jsx";

export default function MessageBubble({ message, onSourceClick }) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      {isUser ? (
        <div className="max-w-[75%] rounded-lg bg-surface-hover px-3.5 py-2 text-base text-foreground">
          {message.content}
        </div>
      ) : (
        <div className="max-w-[85%]">
          {message.rewrittenQuery && (
            <p className="mb-1.5 text-sm text-muted">searched for: {message.rewrittenQuery}</p>
          )}
          {message.error ? (
            <p className="text-base text-danger">{message.content}</p>
          ) : (
            <Markdown>{message.content}</Markdown>
          )}
          {message.sources?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {message.sources.map((source) => (
                <SourceChip key={source} source={source} onClick={onSourceClick} />
              ))}
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}
