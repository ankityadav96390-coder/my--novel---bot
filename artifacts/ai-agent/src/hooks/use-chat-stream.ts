import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getGetGeminiConversationQueryKey, getListGeminiMessagesQueryKey } from '@workspace/api-client-react';

export function useChatStream(conversationId: number) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedContent, setStreamedContent] = useState('');
  const queryClient = useQueryClient();

  const sendMessage = useCallback(async (content: string) => {
    setIsStreaming(true);
    setStreamedContent('');

    try {
      const res = await fetch(`/api/gemini/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      });

      if (!res.ok) throw new Error('Failed to send message');

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          // Keep the last incomplete line in the buffer
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.replace('data: ', '').trim();
              if (!dataStr) continue;
              try {
                const data = JSON.parse(dataStr);
                if (data.done) break;
                if (data.content) {
                  setStreamedContent(prev => prev + data.content);
                }
              } catch (e) {
                console.error('[SSE] Failed to parse chunk:', e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('[Chat] Streaming error:', error);
    } finally {
      setIsStreaming(false);
      // Invalidate both the single conversation and the messages list
      queryClient.invalidateQueries({ queryKey: getGetGeminiConversationQueryKey(conversationId) });
      queryClient.invalidateQueries({ queryKey: getListGeminiMessagesQueryKey(conversationId) });
    }
  }, [conversationId, queryClient]);

  return { sendMessage, isStreaming, streamedContent };
}
