import { useState } from "react";
import { Link } from "react-router-dom";

import Button from "../components/Button.jsx";
import Logo from "../components/Logo.jsx";
import PasswordInput from "../components/PasswordInput.jsx";
import TextInput from "../components/TextInput.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { getErrorMessage } from "../services/api.js";

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login({ email, password });
      // On success, AuthContext's user becomes truthy and PublicOnlyRoute
      // redirects to /app on its own — no navigate() call needed here.
    } catch (err) {
      // /api/auth/login returns a generic 401 without saying which field is
      // wrong, so this is one general error block, not a field-level one.
      setError(getErrorMessage(err, "Incorrect email or password."));
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-bg px-4">
      <Logo className="mb-8" />
      <div className="w-full max-w-[360px] rounded-lg border border-border bg-surface p-6">
        <h1 className="mb-6 text-lg font-medium text-foreground">Log in</h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <TextInput
            label="Email"
            type="email"
            name="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <PasswordInput
            label="Password"
            name="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && (
            <div className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
              {error}
            </div>
          )}

          <Button type="submit" loading={loading} className="mt-1 w-full">
            {loading ? "Logging in…" : "Log in"}
          </Button>
        </form>
      </div>

      <p className="mt-6 text-sm text-muted">
        Don't have an account?{" "}
        <Link to="/register" className="text-accent hover:underline">
          Create one
        </Link>
      </p>
    </div>
  );
}
