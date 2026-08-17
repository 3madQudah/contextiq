import { Link } from "react-router-dom";

import Button from "../Button.jsx";
import BrainMark from "./BrainMark.jsx";

// Shared header for every public page (Landing + the /product, /databases,
// /docs content pages) — one place to keep nav markup identical everywhere,
// per the "same nav across all pages" requirement. `active` highlights the
// current section's link; omit it on Landing (none of the three apply).
const NAV_LINKS = [
  { label: "Product", to: "/product" },
  { label: "Databases", to: "/databases" },
  { label: "Docs", to: "/docs" },
];

export default function PublicNav({ active }) {
  return (
    <nav className="sticky top-0 z-30 border-b border-border/60 bg-bg/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-2">
          <BrainMark size={20} />
          <span className="text-base font-medium text-foreground">ContextIQ</span>
        </Link>

        <div className="hidden items-center md:flex">
          {NAV_LINKS.map(({ label, to }) => (
            <Link
              key={to}
              to={to}
              className={`px-3 py-2 text-sm text-foreground transition-colors hover:opacity-70 ${
                active === to.slice(1) ? "font-medium" : ""
              }`}
            >
              {label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-1">
          <Link
            to="/login"
            className="px-3 py-2 text-sm text-muted transition-colors hover:text-foreground"
          >
            Log in
          </Link>
          <Link to="/register">
            <Button variant="invert" className="text-sm">
              Get started
            </Button>
          </Link>
        </div>
      </div>
    </nav>
  );
}
