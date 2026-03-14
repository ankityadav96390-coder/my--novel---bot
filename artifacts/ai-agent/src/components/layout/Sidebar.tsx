import { Link, useLocation } from "wouter";
import { useListGeminiConversations, useDeleteGeminiConversation, useCreateGeminiConversation } from "@workspace/api-client-react";
import { Plus, MessageSquare, Trash2, X, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface SidebarProps {
  onClose?: () => void;
  isMobile?: boolean;
}

export function Sidebar({ onClose, isMobile }: SidebarProps) {
  const [location, setLocation] = useLocation();
  const { data: conversations, isLoading } = useListGeminiConversations();
  const deleteMutation = useDeleteGeminiConversation();
  const createMutation = useCreateGeminiConversation();
  
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const activeId = location.startsWith("/chat/") ? parseInt(location.split("/")[2]) : null;

  const handleNewChat = async () => {
    // Navigate home, which resets to the new chat screen
    setLocation("/");
    if (onClose) onClose();
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.preventDefault();
    e.stopPropagation();
    setDeletingId(id);
    try {
      await deleteMutation.mutateAsync({ id });
      if (activeId === id) {
        setLocation("/");
      }
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0a0c] border-r border-white/5">
      <div className="p-4 sm:p-6 pb-2 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group cursor-pointer">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg shadow-primary/20 group-hover:scale-105 transition-transform duration-300">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-bold text-lg text-white group-hover:text-primary-foreground transition-colors">Orbit AI</span>
        </Link>
        {isMobile && onClose && (
          <Button variant="ghost" size="icon" onClick={onClose} className="sm:hidden -mr-2">
            <X className="w-5 h-5" />
          </Button>
        )}
      </div>

      <div className="px-4 py-4">
        <Button 
          onClick={handleNewChat} 
          className="w-full justify-start gap-3 bg-white/5 hover:bg-white/10 border border-white/5 text-foreground"
          variant="outline"
        >
          <Plus className="w-4 h-4 text-primary" />
          New Chat
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-1">
        <div className="px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
          Recent Conversations
        </div>
        
        {isLoading ? (
          <div className="space-y-2 px-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 rounded-xl bg-white/5 animate-pulse" />
            ))}
          </div>
        ) : conversations?.length === 0 ? (
          <div className="px-4 py-8 text-center text-sm text-muted-foreground">
            No conversations yet. Start a new chat!
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {conversations?.map((conv) => {
              const isActive = activeId === conv.id;
              const isDeleting = deletingId === conv.id;
              
              return (
                <motion.div
                  key={conv.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                >
                  <Link 
                    href={`/chat/${conv.id}`}
                    onClick={() => onClose?.()}
                    className={cn(
                      "group flex flex-col gap-1 px-3 py-2.5 rounded-xl transition-all duration-200 cursor-pointer relative overflow-hidden",
                      isActive 
                        ? "bg-primary/10 border border-primary/20" 
                        : "hover:bg-white/5 border border-transparent"
                    )}
                  >
                    {isActive && (
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-full" />
                    )}
                    
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 overflow-hidden">
                        <MessageSquare className={cn(
                          "w-4 h-4 shrink-0 transition-colors",
                          isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                        )} />
                        <span className={cn(
                          "text-sm truncate font-medium transition-colors",
                          isActive ? "text-primary-foreground" : "text-foreground/80 group-hover:text-foreground"
                        )}>
                          {conv.title || "New Conversation"}
                        </span>
                      </div>
                      
                      <button
                        onClick={(e) => handleDelete(e, conv.id)}
                        disabled={isDeleting}
                        className={cn(
                          "opacity-0 group-hover:opacity-100 p-1.5 -mr-1.5 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all focus:opacity-100 outline-none",
                          isDeleting && "opacity-100"
                        )}
                      >
                        {isDeleting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                    
                    <span className="text-[10px] text-muted-foreground pl-6">
                      {formatDistanceToNow(new Date(conv.createdAt), { addSuffix: true })}
                    </span>
                  </Link>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
