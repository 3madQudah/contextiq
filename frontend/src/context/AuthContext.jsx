import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { decodeJwtPayload } from "../lib/jwt.js";
import { clearToken, getToken, loginUser, registerUser, setToken } from "../services/api.js";

const AuthContext = createContext(null);
const USER_KEY = "contextiq.user";

function loadPersistedUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function persistUser(user) {
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  else localStorage.removeItem(USER_KEY);
}

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session on mount: a token alone isn't enough to trust — check it
  // hasn't expired before treating the user as signed in.
  useEffect(() => {
    const storedToken = getToken();
    if (storedToken) {
      const payload = decodeJwtPayload(storedToken);
      const isExpired = !payload?.exp || payload.exp * 1000 < Date.now();
      if (isExpired) {
        clearToken();
        persistUser(null);
      } else {
        setTokenState(storedToken);
        setUser(loadPersistedUser());
      }
    }
    setLoading(false);
  }, []);

  async function login({ email, password }) {
    const { access_token } = await loginUser({ email, password });
    setToken(access_token);
    const payload = decodeJwtPayload(access_token);
    // Login only returns a token, no user object (see lib/user.js for why) —
    // the email typed into the form is the only identifying info we have.
    const nextUser = { id: payload?.sub ?? null, email };
    persistUser(nextUser);
    setTokenState(access_token);
    setUser(nextUser);
  }

  async function register({ first_name, last_name, email, password }) {
    const created = await registerUser({ first_name, last_name, email, password });
    // Register returns the full user but no token; log in immediately after
    // so creating an account lands the user in the app, not back at a form.
    const { access_token } = await loginUser({ email, password });
    setToken(access_token);
    const nextUser = {
      id: created.id,
      email: created.email,
      first_name: created.first_name,
      last_name: created.last_name,
    };
    persistUser(nextUser);
    setTokenState(access_token);
    setUser(nextUser);
  }

  function logout() {
    clearToken();
    persistUser(null);
    setTokenState(null);
    setUser(null);
  }

  const value = useMemo(
    () => ({ user, token, loading, login, register, logout }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
