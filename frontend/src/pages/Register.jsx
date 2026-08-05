import { useState } from "react";
import { Link } from "react-router-dom";

import Button from "../components/Button.jsx";
import Logo from "../components/Logo.jsx";
import PasswordInput from "../components/PasswordInput.jsx";
import TextInput from "../components/TextInput.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { getErrorMessage } from "../services/api.js";

const MIN_PASSWORD_LENGTH = 8;

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

  async function handleSubmit(e) {
    e.preventDefault();
    setEmailError("");
    setPasswordError("");
    setGeneralError("");

    // The backend has no password-length rule at all — this is purely a
    // client-side UX guard, enforced here since nothing stops a short
    // password from reaching the API otherwise.
    if (password.length < MIN_PASSWORD_LENGTH) {
      setPasswordError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }

    setLoading(true);
    try {
      await register({ first_name: firstName, last_name: lastName, email, password });
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
    <div className="flex min-h-screen flex-col items-center justify-center bg-bg px-4">
      <Logo className="mb-8" />
      <div className="w-full max-w-[360px] rounded-lg border border-border bg-surface p-6">
        <h1 className="mb-1.5 text-lg font-medium text-foreground">Create your account</h1>
        <p className="mb-6 text-sm text-muted">
          Your documents stay private to your account — no one else can see them.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <TextInput
              label="First name"
              name="first_name"
              autoComplete="given-name"
              required
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
            />
            <TextInput
              label="Last name"
              name="last_name"
              autoComplete="family-name"
              required
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
            />
          </div>

          <TextInput
            label="Email"
            type="email"
            name="email"
            autoComplete="email"
            required
            error={emailError}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <PasswordInput
            label="Password"
            name="password"
            autoComplete="new-password"
            required
            error={passwordError}
            hint={passwordError ? undefined : `At least ${MIN_PASSWORD_LENGTH} characters.`}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {generalError && (
            <div className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
              {generalError}
            </div>
          )}

          <Button type="submit" loading={loading} className="mt-1 w-full">
            {loading ? "Creating account…" : "Create account"}
          </Button>
        </form>
      </div>

      <p className="mt-6 text-sm text-muted">
        Already have an account?{" "}
        <Link to="/login" className="text-accent hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
