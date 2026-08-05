import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import FullPageSpinner from "./FullPageSpinner.jsx";

export default function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) return <FullPageSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}
