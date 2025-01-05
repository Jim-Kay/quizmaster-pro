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
  const MIN_EXECUTION_INTERVAL = 1000; // 1 second minimum between executions

  const createExecution = useCallback(async (flowName: string, initialState: any) => {
    if (!session?.accessToken) return null;

    // Check if execution is in progress or if not enough time has passed
    const now = Date.now();
    if (executionInProgressRef.current || now - lastExecutionTimeRef.current < MIN_EXECUTION_INTERVAL) {
      console.log('Execution in progress or too soon, skipping...');
      return null;
    }

    try {
      executionInProgressRef.current = true;
      setIsGenerating(true);
      lastExecutionTimeRef.current = now;

      const idempotencyKey = Buffer.from(JSON.stringify({
        ...initialState,
        timestamp: Math.floor(now / MIN_EXECUTION_INTERVAL) // Round to nearest interval
      })).toString('base64');

      const createResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions`, {
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
    }
  }, [session?.accessToken, onError]);

  const startExecution = useCallback(async (executionId: string) => {
    if (!session?.accessToken) return false;

    try {
      const startResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions/${executionId}/start`, {
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
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start execution';
      onError?.(message);
      executionInProgressRef.current = false;
      return false;
    }
  }, [session?.accessToken, onError]);

  const pollStatus = useCallback(async () => {
    if (!session?.accessToken || !executionId) return;

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/flows/executions/${executionId}`, {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`
        }
      });

      if (response.status === 401) {
        throw new Error('Unauthorized. Please sign in again.');
      }

      const execution: FlowExecution = await response.json();
      setStatus(execution.status);

      if (execution.status === 'completed' || execution.status === 'failed') {
        setIsGenerating(false);
        executionInProgressRef.current = false;
        if (execution.status === 'failed' && execution.error) {
          onError?.(execution.error);
        }
      }

      return execution;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to poll status';
      onError?.(message);
      setIsGenerating(false);
      executionInProgressRef.current = false;
      return null;
    }
  }, [session?.accessToken, executionId, onError]);

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
