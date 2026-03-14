import { useState } from "react";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sidebar } from "./Sidebar";
import { motion, AnimatePresence } from "framer-motion";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden relative">
      {/* Desktop Sidebar */}
      <div className="hidden md:block w-72 shrink-0 z-10">
        <Sidebar />
      </div>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsMobileMenuOpen(false)}
            />
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="md:hidden fixed inset-y-0 left-0 z-50 w-[280px] shadow-2xl"
            >
              <Sidebar isMobile onClose={() => setIsMobileMenuOpen(false)} />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 z-0">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center h-14 px-4 border-b border-white/5 bg-[#0a0a0c]/80 backdrop-blur-md sticky top-0 z-30">
          <Button variant="ghost" size="icon" onClick={() => setIsMobileMenuOpen(true)} className="-ml-2">
            <Menu className="w-5 h-5" />
          </Button>
          <span className="font-display font-semibold text-foreground ml-2">Orbit AI</span>
        </div>

        <main className="flex-1 relative flex flex-col h-full overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
