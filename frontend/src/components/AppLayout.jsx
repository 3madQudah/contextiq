import { AnimatePresence, motion } from "framer-motion";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { Outlet } from "react-router-dom";

import { AppDataProvider } from "../context/AppDataContext.jsx";
import DemoBanner from "./DemoBanner.jsx";
import Logo from "./Logo.jsx";
import Sidebar from "./Sidebar.jsx";

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <AppDataProvider>
      <div className="flex h-screen overflow-hidden bg-bg">
        <div className="hidden md:flex md:w-[200px] md:shrink-0 md:flex-col md:border-r md:border-border">
          <Sidebar />
        </div>

        <AnimatePresence>
          {mobileOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="fixed inset-0 z-40 bg-black/40 md:hidden"
                onClick={() => setMobileOpen(false)}
              />
              <motion.div
                initial={{ x: -240, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -240, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="fixed inset-y-0 left-0 z-50 w-[240px] border-r border-border md:hidden"
              >
                <div className="flex justify-end px-2 pt-2">
                  <button
                    type="button"
                    aria-label="Close sidebar"
                    onClick={() => setMobileOpen(false)}
                    className="flex h-8 w-8 items-center justify-center rounded-md text-muted hover:bg-surface-hover"
                  >
                    <X size={16} strokeWidth={1.5} />
                  </button>
                </div>
                <Sidebar onNavigate={() => setMobileOpen(false)} />
              </motion.div>
            </>
          )}
        </AnimatePresence>

        <div className="flex flex-1 flex-col overflow-hidden">
          <DemoBanner />

          <div className="flex items-center gap-3 border-b border-border px-4 py-3 md:hidden">
            <button
              type="button"
              aria-label="Open sidebar"
              onClick={() => setMobileOpen(true)}
              className="flex h-8 w-8 items-center justify-center rounded-md text-muted hover:bg-surface-hover"
            >
              <Menu size={18} strokeWidth={1.5} />
            </button>
            <Logo size="sm" />
          </div>

          <div className="flex-1 overflow-hidden">
            <Outlet />
          </div>
        </div>
      </div>
    </AppDataProvider>
  );
}
