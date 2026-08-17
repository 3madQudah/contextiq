import { IconCheck, IconX } from "@tabler/icons-react";

// Mirrors the real enforcement in backend/auth/schemas.py
// (_password_requirement_failures) exactly — this is the UX nicety that
// shows live feedback and gates the submit button; the backend validator
// is what actually enforces it (never trust client-side validation alone).
export const PASSWORD_RULES = [
  { key: "length", label: "At least 12 characters", test: (pw) => pw.length >= 12 },
  { key: "upper", label: "One uppercase letter", test: (pw) => /[A-Z]/.test(pw) },
  { key: "lower", label: "One lowercase letter", test: (pw) => /[a-z]/.test(pw) },
  { key: "digit", label: "One digit", test: (pw) => /\d/.test(pw) },
  {
    key: "special",
    label: "One special character (!@#$%^&*()_+-=)",
    test: (pw) => /[!@#$%^&*()_+\-=]/.test(pw),
  },
];

export function isPasswordValid(password) {
  return PASSWORD_RULES.every((rule) => rule.test(password));
}

export default function PasswordStrengthMeter({ password }) {
  if (!password) return null;

  return (
    <ul className="mt-1.5 flex flex-col gap-1">
      {PASSWORD_RULES.map((rule) => {
        const passed = rule.test(password);
        return (
          <li
            key={rule.key}
            className={`flex items-center gap-1.5 text-xs ${passed ? "text-success" : "text-muted"}`}
          >
            {passed ? (
              <IconCheck size={12} stroke={2.5} className="shrink-0" />
            ) : (
              <IconX size={12} stroke={2} className="shrink-0" />
            )}
            {rule.label}
          </li>
        );
      })}
    </ul>
  );
}
