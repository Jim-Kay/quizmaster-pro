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
    if (!session?.accessToken) {
      onError?.('Not authenticated');
      return;
    }

    try {
      // Close existing WebSocket if any
      if (webSocketRef.current) {
        webSocketRef.current.close();
      }

      // Reset reconnect attempts
      reconnectAttemptsRef.current = 0;

      // Create new WebSocket connection with token
      const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(':3000', ':8000') || 'http://localhost:8000';
      const wsUrl = `${apiUrl.replace('http:', 'ws:').replace('https:', 'wss:')}/api/flows/executions/${executionId}/logs/ws`;
      
      // Add token as query parameter - no need to URL encode since it's already properly formatted
      const url = new URL(wsUrl);
      url.searchParams.append('token', `Bearer ${session.accessToken}`);
      
      console.log('Connecting to WebSocket...', url.toString());
      const ws = new WebSocket(url.toString());
      webSocketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setLogs(''); // Clear logs on new connection
      };

      ws.onmessage = (event) => {
        try {
          const log = JSON.parse(event.data);
          if (log.error) {
            onError?.(log.error);
            return;
          }
          
          setLogs(prev => {
            // Format log message based on level and timestamp
            const timestamp = new Date(log.timestamp).toLocaleTimeString();
            const level = (log.level || 'INFO').toUpperCase();
            const formattedMessage = `[${timestamp}] ${level}: ${log.message}\n`;
            return prev + formattedMessage;
          });
        } catch (error) {
          console.error('Error parsing log message:', error);
          onError?.('Failed to parse log message');
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.('Failed to connect to log stream');
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        
        // Handle specific close codes
        switch (event.code) {
          case 4001:
            onError?.('Authentication failed. Please sign in again.');
            return;
          case 4004:
            onError?.('Flow execution not found or access denied');
            return;
          case 4005:
            onError?.('Error verifying flow execution');
            return;
          case 1000:
            console.log('WebSocket closed normally');
            return;
          default:
            // Attempt to reconnect for other codes
            if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
              console.log(`Reconnecting... Attempt ${reconnectAttemptsRef.current + 1}/${MAX_RECONNECT_ATTEMPTS}`);
              reconnectTimeoutRef.current = setTimeout(() => {
                reconnectAttemptsRef.current++;
                startStream(executionId);
              }, RECONNECT_DELAY);
            } else {
              onError?.('Maximum reconnection attempts reached');
            }
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
