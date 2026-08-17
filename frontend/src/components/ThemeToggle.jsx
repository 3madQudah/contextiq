import { AnimatePresence, motion } from "motion/react";
import { Moon, Sun } from "lucide-react";

import { useTheme } from "../context/ThemeContext.jsx";

export default function ThemeToggle({ className = "" }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <motion.button
      type="button"
      onClick={toggleTheme}
      aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      whileHover={{ scale: 1.08 }}
      whileTap={{ scale: 0.9 }}
      className={`relative inline-flex h-8 w-8 items-center justify-center overflow-hidden rounded-md text-muted transition-colors hover:bg-surface-hover hover:text-foreground ${className}`}
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={theme}
          initial={{ rotate: -90, opacity: 0, scale: 0.6 }}
          animate={{ rotate: 0, opacity: 1, scale: 1 }}
          exit={{ rotate: 90, opacity: 0, scale: 0.6 }}
          transition={{ duration: 0.2 }}
          className="flex items-center justify-center"
        >
          {theme === "dark" ? <Sun size={16} strokeWidth={1.5} /> : <Moon size={16} strokeWidth={1.5} />}
        </motion.span>
      </AnimatePresence>
    </motion.button>
  );
}
