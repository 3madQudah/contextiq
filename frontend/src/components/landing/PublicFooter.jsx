import { IconBrandGithub, IconBrandLinkedin, IconMail } from "@tabler/icons-react";
import { motion } from "motion/react";

import { easeOut } from "../../lib/motion.js";

const CONTACT_LINKS = [
  { icon: IconMail, label: "qudahemad@yahoo.com", href: "mailto:qudahemad@yahoo.com" },
  { icon: IconBrandGithub, label: "github.com/3madQudah", href: "https://github.com/3madQudah" },
  {
    icon: IconBrandLinkedin,
    label: "linkedin.com/in/emadalqudah",
    href: "https://www.linkedin.com/in/emadalqudah",
  },
];

// Shared footer for every public page — same "about" block that used to
// live only in Landing.jsx, now reused by /product, /databases and /docs
// too so the whole public site closes consistently.
export default function PublicFooter() {
  return (
    <motion.footer
      initial="initial"
      whileInView="animate"
      viewport={{ once: true, margin: "-60px" }}
      variants={{
        initial: { opacity: 0, y: 16 },
        animate: { opacity: 1, y: 0, transition: { duration: 0.55, ease: easeOut, delay: 0.1 } },
      }}
      className="border-t border-border"
    >
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-5 px-6 py-12 text-center sm:flex-row sm:items-center sm:justify-center sm:text-left">
        {/* Fixed black/white, not the accent token — matches the literal
            corrective spec, same fixed-color treatment as the "Get started"
            button and chat mockup above. */}
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-black text-base font-semibold text-white">
          EQ
        </div>
        <div className="flex flex-col items-center gap-2 sm:items-start">
          <p className="text-base font-semibold text-foreground">Built by Emad Qudah</p>
          <p className="max-w-lg text-sm text-muted">
            AI Engineer and Data Science graduate from The University of Jordan, focused on
            Generative AI, RAG pipelines, and LLM application development.
          </p>
          <div className="mt-1 flex flex-col items-center gap-2 sm:flex-row sm:gap-5">
            {CONTACT_LINKS.map(({ icon: Icon, label, href }) => (
              <a
                key={label}
                href={href}
                target={href.startsWith("http") ? "_blank" : undefined}
                rel={href.startsWith("http") ? "noreferrer" : undefined}
                className="inline-flex items-center gap-1.5 text-sm text-muted transition-colors hover:text-foreground"
              >
                <Icon size={15} stroke={1.75} />
                {label}
              </a>
            ))}
          </div>
        </div>
      </div>
    </motion.footer>
  );
}
