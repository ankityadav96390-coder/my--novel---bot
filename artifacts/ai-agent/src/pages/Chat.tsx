import { useEffect, useRef, useState } from "react";
import { useParams } from "wouter";
import { useListGeminiMessages } from "@workspace/api-client-react";
import { useChatStream } from "@/hooks/use-chat-stream";
import { ChatInput } from "@/components/chat/ChatInput";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function Chat() {
  const { id } = useParams();
  const conversationId = id ? parseInt(id) : 0;
  
  const { data: messages = [], isLoading } = useListGeminiMessages(conversationId);
  const { sendMessage, isStreaming, streamedContent } = useChatStream(conversationId);
  
  const [optimisticMsg, setOptimisticMsg] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const initialMessageSent = useRef(false);

  // Scroll to bottom when new messages arrive or streaming updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamedContent, optimisticMsg]);

  // Handle URL query param for initial auto-send
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const initialQuery = params.get("q");

    if (initialQuery && !initialMessageSent.current && !isStreaming) {
      initialMessageSent.current = true;
      
      // Clean up URL
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.delete("q");
      window.history.replaceState({}, "", newUrl);

      // Trigger send
      handleSend(initialQuery);
    }
  }, [conversationId, isStreaming]);

  const handleSend = async (content: string) => {
    setOptimisticMsg(content);
    await sendMessage(content);
    setOptimisticMsg("");
  };

  return (
    <div className="flex-1 flex flex-col h-full relative">
      {/* Scrollable Messages Area */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {isLoading && messages.length === 0 ? (
          <div className="flex-1 flex items-center justify-center h-full min-h-[50vh]">
            <Loader2 className="w-8 h-8 text-primary/50 animate-spin" />
          </div>
        ) : (
          <div className="flex flex-col pb-32">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            
            {/* Optimistic User Message */}
            {optimisticMsg && (
              <MessageBubble message={{ role: "user", content: optimisticMsg }} />
            )}
            
            {/* Streaming AI Message */}
            {(isStreaming || streamedContent) && (
              <MessageBubble 
                message={{ role: "assistant", content: streamedContent }} 
                isStreaming 
              />
            )}
            
            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}
      </div>

      {/* Sticky Bottom Input Area */}
      <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-background via-background to-transparent pt-10 pb-6 px-4">
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="max-w-4xl mx-auto"
        >
          <ChatInput 
            onSend={handleSend} 
            disabled={isStreaming} 
            autoFocus 
          />
        </motion.div>
      </div>
    </div>
  );
}
