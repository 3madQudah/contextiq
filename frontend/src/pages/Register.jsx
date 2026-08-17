import { useState } from "react";
import { Link } from "react-router-dom";

import AuthBrand from "../components/landing/AuthBrand.jsx";
import Button from "../components/Button.jsx";
import PasswordInput from "../components/PasswordInput.jsx";
import PasswordStrengthMeter, { isPasswordValid } from "../components/PasswordStrengthMeter.jsx";
import TextInput from "../components/TextInput.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { getErrorMessage } from "../services/api.js";

const LABEL_CLASS = "text-sm font-semibold text-foreground";

export default function Register() {
  const { register } = useAuth();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [generalError, setGeneralError] = useState("");

  const passwordValid = isPasswordValid(password);

  async function handleSubmit(e) {
    e.preventDefault();
    setEmailError("");
    setPasswordError("");
    setGeneralError("");

    // The real enforcement is server-side (backend/auth/schemas.py) --
    // this is a defense-in-depth guard alongside the disabled submit
    // button below, not the source of truth. If it's ever wrong for some
    // reason, the backend still rejects a weak password with its own
    // clear per-requirement message via generalError below.
    if (!passwordValid) {
      setPasswordError("Password doesn't meet all the requirements below.");
      return;
    }

    setLoading(true);
    try {
      await register({ first_name: firstName, last_name: lastName, email, password });
      // On success, AuthContext's user becomes truthy and PublicOnlyRoute
      // redirects to /app on its own — no navigate() call needed here.
    } catch (err) {
      const message = getErrorMessage(err);
      // /api/auth/register returns 400 specifically for a duplicate email —
      // that IS field-specific, so it goes inline under the email input.
      if (err.response?.status === 400) {
        setEmailError(message);
      } else {
        setGeneralError(message);
      }
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-surface-hover px-4 py-10">
      <AuthBrand className="mb-8" />

      <div className="w-full max-w-[360px] rounded-xl border border-border bg-surface p-6">
        <h1 className="text-center text-lg font-bold text-foreground">Create your account</h1>
        <p className="mt-1.5 text-center text-sm text-muted">
          Your documents stay private to your account.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <TextInput
              label="First name"
              name="first_name"
              autoComplete="given-name"
              placeholder="First name"
              required
              labelClassName={LABEL_CLASS}
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
            />
            <TextInput
              label="Last name"
              name="last_name"
              autoComplete="family-name"
              placeholder="Last name"
              required
              labelClassName={LABEL_CLASS}
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
            />
          </div>

          <TextInput
            label="Email"
            type="email"
            name="email"
            autoComplete="email"
            placeholder="you@example.com"
            required
            error={emailError}
            labelClassName={LABEL_CLASS}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <div>
            <PasswordInput
              label="Password"
              name="password"
              autoComplete="new-password"
              required
              error={passwordError}
              labelClassName={LABEL_CLASS}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <PasswordStrengthMeter password={password} />
          </div>

          {generalError && (
            <div className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
              {generalError}
            </div>
          )}

          <Button
            type="submit"
            variant="invert"
            loading={loading}
            disabled={!passwordValid}
            className="mt-1 w-full"
          >
            {loading ? "Creating account…" : "Create account"}
          </Button>
        </form>
      </div>

      <p className="mt-6 text-sm text-muted">
        Already have an account?{" "}
        <Link to="/login" className="font-bold text-foreground hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
