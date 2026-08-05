import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// No dev-server proxy: axios talks directly to VITE_API_BASE_URL (see
// src/services/api.js), and the backend's CORS middleware already allows
// the Vite dev origin (FRONTEND_ORIGIN in backend/.env).
export default defineConfig({
  plugins: [react()],
});
