import { useState, useCallback, useRef } from 'react';
import { useSession } from 'next-auth/react';

interface FlowExecution {
  id: string;
  flow_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error?: string;
}

interface UseFlowExecutionOptions {
  onError?: (error: string) => void;
}

export function useFlowExecution({ onError }: UseFlowExecutionOptions = {}) {
  const { data: session } = useSession();
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const executionInProgressRef = useRef(false);
  const lastExecutionTimeRef = useRef(0);
  const MIN_EXECUTION_INTERVAL = 3000; // 3 seconds minimum between executions
  const executionStateRef = useRef<'creating' | 'starting' | 'running' | null>(null);

  const createExecution = useCallback(async (flowName: string, initialState: any) => {
    if (!session?.accessToken) return null;

    // Check execution state
    if (executionStateRef.current !== null) {
      console.log(`Execution already in ${executionStateRef.current} state, skipping...`);
      return null;
    }

    // Check if not enough time has passed
    const now = Date.now();
    if (now - lastExecutionTimeRef.current < MIN_EXECUTION_INTERVAL) {
      console.log('Too soon since last execution, skipping...');
      return null;
    }

    try {
      executionStateRef.current = 'creating';
      setIsGenerating(true);
      lastExecutionTimeRef.current = now;

      // Create a more stable idempotency key
      const idempotencyKey = Buffer.from(JSON.stringify({
        flow_name: flowName,
        ...initialState,
        // Round to nearest 5 seconds to prevent rapid retries
        timestamp: Math.floor(now / 5000)
      })).toString('base64');

      const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(':3000', ':8000') || 'http://localhost:8000';
      const createResponse = await fetch(`${apiUrl}/api/flows/executions`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.accessToken}`,
          'X-Idempotency-Key': idempotencyKey
        },
        body: JSON.stringify({
          flow_name: flowName,
          initial_state: initialState,
          use_cache: true
        })
      });

      if (createResponse.status === 401) {
        throw new Error('Unauthorized. Please sign in again.');
      }

      if (!createResponse.ok) {
        throw new Error(`Failed to create flow: ${createResponse.statusText}`);
      }

      const data = await createResponse.json();
      return data as FlowExecution;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create execution';
      onError?.(message);
      return null;
    } finally {
      executionStateRef.current = null;
      setIsGenerating(false);
    }
  }, [session?.accessToken, onError]);

  const startExecution = useCallback(async (executionId: string) => {
    if (!session?.accessToken) return false;

    // Check execution state
    if (executionStateRef.current !== null) {
      console.log(`Execution already in ${executionStateRef.current} state, skipping...`);
      return false;
    }

    try {
      executionStateRef.current = 'starting';
      const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(':3000', ':8000') || 'http://localhost:8000';
      const startResponse = await fetch(`${apiUrl}/api/flows/executions/${executionId}/start`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.accessToken}`
        },
        body: JSON.stringify({
          background_tasks: true
        })
      });

      if (startResponse.status === 401) {
        throw new Error('Unauthorized. Please sign in again.');
      }

      if (!startResponse.ok) {
        throw new Error(`Failed to start execution: ${startResponse.statusText}`);
      }

      setExecutionId(executionId);
      setStatus('running');
      executionStateRef.current = 'running';
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start execution';
      onError?.(message);
      executionStateRef.current = null;
      return false;
    }
  }, [session?.accessToken, onError]);

  const pollStatus = useCallback(async () => {
    if (!executionId || !session?.accessToken) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(':3000', ':8000') || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/flows/executions/${executionId}`, {
        headers: { 
          'Authorization': `Bearer ${session.accessToken}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to poll status: ${response.statusText}`);
      }

      const data = await response.json();
      setStatus(data.status);

      // Clear execution state if we're done
      if (data.status === 'completed' || data.status === 'failed') {
        executionStateRef.current = null;
        setIsGenerating(false);
      }
    } catch (error) {
      console.error('Error polling status:', error);
    }
  }, [executionId, session?.accessToken]);

  return {
    executionId,
    status,
    isGenerating,
    createExecution,
    startExecution,
    pollStatus,
    setStatus,
    setIsGenerating
  };
}
