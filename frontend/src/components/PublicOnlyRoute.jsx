import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import FullPageSpinner from "./FullPageSpinner.jsx";

// Wraps /, /login, /register: bounce already-authed users into the app.
export default function PublicOnlyRoute() {
  const { user, loading } = useAuth();

  if (loading) return <FullPageSpinner />;
  if (user) return <Navigate to="/app" replace />;
  return <Outlet />;
}
