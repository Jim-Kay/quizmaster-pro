import { useState, useRef, useCallback, useEffect } from 'react';
import { useSession } from 'next-auth/react';

interface UseLogStreamOptions {
  onError?: (error: string) => void;
}

export function useLogStream({ onError }: UseLogStreamOptions = {}) {
  const { data: session } = useSession();
  const [logs, setLogs] = useState<string>('');
  const webSocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 1000; // 1 second

  const startStream = useCallback(async (executionId: string) => {
    if (!session?.accessToken) return;

    try {
      // Close existing WebSocket if any
      if (webSocketRef.current) {
        webSocketRef.current.close();
      }

      // Reset reconnect attempts
      reconnectAttemptsRef.current = 0;

      // Create new WebSocket connection
      const wsUrl = `${process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws')}/api/flows/executions/${executionId}/logs/ws`;
      const ws = new WebSocket(wsUrl);
      webSocketRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const log = JSON.parse(event.data);
          setLogs(prev => {
            // Format log message based on level
            const timestamp = new Date(log.timestamp).toLocaleTimeString();
            const level = log.level.toUpperCase();
            const formattedMessage = `[${timestamp}] ${level}: ${log.message}\n`;
            return prev + formattedMessage;
          });
        } catch (error) {
          console.error('Error parsing log message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.('Failed to connect to log stream');
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        // Attempt to reconnect if not manually closed
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            startStream(executionId);
          }, RECONNECT_DELAY);
        }
      };

    } catch (error) {
      console.error('Error starting log stream:', error);
      onError?.(error instanceof Error ? error.message : 'Failed to start log stream');
    }
  }, [session?.accessToken, onError]);

  const stopStream = useCallback(() => {
    // Clear any pending reconnect attempts
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    reconnectAttemptsRef.current = MAX_RECONNECT_ATTEMPTS; // Prevent further reconnects

    if (webSocketRef.current) {
      webSocketRef.current.close();
      webSocketRef.current = null;
    }
    setLogs('');
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (webSocketRef.current) {
        webSocketRef.current.close();
      }
    };
  }, []);

  return {
    logs,
    setLogs,
    startStream,
    stopStream
  };
}
