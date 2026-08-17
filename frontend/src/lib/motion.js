// Shared motion tokens so every page/component animates on the same
// rhythm — one place to tune durations/easing instead of magic numbers
// scattered through each file. Reduced-motion is handled globally via
// <MotionConfig reducedMotion="user"> in main.jsx, so these don't need to
// check prefers-reduced-motion themselves.

// Entrance easing: ease-out-ish cubic-bezier, snappier than the default.
export const easeOut = [0.22, 1, 0.36, 1];

export const springSnappy = { type: "spring", stiffness: 420, damping: 32, mass: 0.8 };
export const springSoft = { type: "spring", stiffness: 300, damping: 28 };

// Page-level fade/slide, used for the content that swaps inside AppLayout's
// <Outlet/> and for the public marketing/auth pages.
export const pageVariants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.22, ease: easeOut } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.14, ease: easeOut } },
};

// Stagger container/item pair for lists (conversations, documents,
// database connections, feature grids). Spread `staggerContainer` on the
// parent and `staggerItem` on each child.
export const staggerContainer = {
  initial: {},
  animate: { transition: { staggerChildren: 0.045, delayChildren: 0.02 } },
};

export const staggerItem = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.22, ease: easeOut } },
  exit: { opacity: 0, y: -4, transition: { duration: 0.15 } },
};

// Fade+lift used for chat/database-answer message bubbles as they arrive.
export const messageVariants = {
  initial: { opacity: 0, y: 8, scale: 0.99 },
  animate: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.22, ease: easeOut } },
};

// Card/button micro-interaction: subtle lift + scale, not a full bounce.
export const liftHover = { y: -2, transition: springSnappy };
export const tapScale = { scale: 0.97, transition: { duration: 0.1 } };
export const buttonTap = { scale: 0.96 };
export const buttonHover = { scale: 1.015 };
