import { Link } from "react-router-dom";

import BrainMark from "./BrainMark.jsx";

// Minimal brand mark for the auth pages (Login/Register) — same exact brain
// SVG + wordmark as PublicNav, but without the full nav bar (no Product/
// Databases/Docs links, no Log in/Get started buttons — those don't belong
// mid-auth-flow). Links back to the landing page.
export default function AuthBrand({ className = "" }) {
  return (
    <Link to="/" className={`flex items-center gap-2 ${className}`}>
      <BrainMark size={22} />
      <span className="text-base font-medium text-foreground">ContextIQ</span>
    </Link>
  );
}
