import { type GeminiMessage } from "@workspace/api-client-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Sparkles, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface MessageBubbleProps {
  message: Pick<GeminiMessage, 'role' | 'content'>;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isAI = message.role === "assistant" || message.role === "model";

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex w-full gap-4 sm:gap-6 py-6 px-4 sm:px-8",
        isAI ? "bg-transparent" : "bg-white/[0.02]"
      )}
    >
      <div className="max-w-4xl mx-auto w-full flex gap-4 sm:gap-6">
        <div className="shrink-0 mt-1">
          {isAI ? (
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg shadow-primary/20">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-xl bg-secondary border border-white/10 flex items-center justify-center shadow-sm">
              <User className="w-4 h-4 text-muted-foreground" />
            </div>
          )}
        </div>
        
        <div className="flex-1 min-w-0 pt-1.5 space-y-2">
          {isAI ? (
            <div className="prose-custom">
              {message.content ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              ) : (
                isStreaming && (
                  <div className="flex gap-1 items-center h-6 text-primary">
                    <div className="w-2 h-2 rounded-full bg-primary/60 typing-dot" />
                    <div className="w-2 h-2 rounded-full bg-primary/60 typing-dot" />
                    <div className="w-2 h-2 rounded-full bg-primary/60 typing-dot" />
                  </div>
                )
              )}
            </div>
          ) : (
            <div className="text-[15px] leading-relaxed text-foreground/90 whitespace-pre-wrap">
              {message.content}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
