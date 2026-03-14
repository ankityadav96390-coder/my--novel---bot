import { useState, useRef, useEffect } from "react";
import { Send, CornerDownLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}

export function ChatInput({ onSend, disabled, placeholder = "Message Orbit AI...", className, autoFocus }: ChatInputProps) {
  const [content, setContent] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resizeTextarea = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  useEffect(() => {
    resizeTextarea();
  }, [content]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (content.trim() && !disabled) {
      onSend(content.trim());
      setContent("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className={cn("relative w-full max-w-4xl mx-auto flex flex-col", className)}>
      <div className="relative flex items-end w-full bg-secondary/50 backdrop-blur-xl border border-white/10 rounded-3xl shadow-xl shadow-black/20 focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/50 transition-all duration-300">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          autoFocus={autoFocus}
          rows={1}
          className="w-full max-h-[200px] min-h-[56px] py-4 pl-6 pr-14 bg-transparent text-foreground placeholder:text-muted-foreground resize-none focus:outline-none text-[15px] leading-relaxed scrollbar-thin rounded-3xl"
        />
        
        <div className="absolute right-3 bottom-2.5">
          <Button
            type="submit"
            size="icon"
            disabled={!content.trim() || disabled}
            className={cn(
              "w-9 h-9 rounded-2xl transition-all duration-300",
              content.trim() && !disabled 
                ? "bg-primary text-white shadow-md shadow-primary/30 hover:scale-105" 
                : "bg-white/5 text-muted-foreground/50 pointer-events-none"
            )}
          >
            <Send className="w-4 h-4 ml-0.5" />
          </Button>
        </div>
      </div>
      <div className="text-center mt-3">
        <p className="text-[11px] font-medium text-muted-foreground/50 flex items-center justify-center gap-1.5">
          Orbit AI can make mistakes. Consider verifying important information.
        </p>
      </div>
    </form>
  );
}
