'use client'

import { useState, useEffect, useRef } from 'react';
import { PencilIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { topicsApi } from '@/api/topics';

interface PoemGeneratorProps {
  topicId: string;
}

interface FlowExecution {
  id: string;
  flow_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error?: string;
}

interface Topic {
  topic_id: string;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export function PoemGenerator({ topicId }: PoemGeneratorProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [logs, setLogs] = useState<string>('');
  const [status, setStatus] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const readerRef = useRef<ReadableStreamDefaultReader | null>(null);

  const { data: topic } = useQuery<Topic>({
    queryKey: ['topic', topicId],
    queryFn: () => topicsApi.getTopic(topicId),
    retry: 1,
    staleTime: 30000,
  });

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Cleanup function for the reader
  useEffect(() => {
    return () => {
      if (readerRef.current) {
        readerRef.current.cancel();
      }
    };
  }, []);

  // Poll for status when execution is running
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (executionId && status !== 'completed' && status !== 'failed') {
      interval = setInterval(async () => {
        try {
          console.log(`Polling status for execution ${executionId}...`);
          const response = await fetch(`/api/flows/executions/${executionId}`);
          const execution: FlowExecution = await response.json();
          console.log(`Current status: ${execution.status}`);
          setStatus(execution.status);
          if (execution.status === 'completed' || execution.status === 'failed') {
            console.log(`Execution ${executionId} ${execution.status}`);
            if (execution.status === 'failed' && execution.error) {
              setError(execution.error);
            }
            clearInterval(interval);
            setIsGenerating(false);
          }
        } catch (error) {
          console.error('Error polling status:', error);
          setError('Failed to poll execution status');
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [executionId, status]);

  const startLogStream = async (executionId: string) => {
    try {
      console.log(`Starting log stream for execution ${executionId}...`);
      const logsResponse = await fetch(`/api/flows/executions/${executionId}/logs`);
      
      if (!logsResponse.ok) {
        throw new Error(`Failed to fetch logs: ${logsResponse.statusText}`);
      }
      
      if (!logsResponse.body) {
        throw new Error('No response body received');
      }

      const reader = logsResponse.body.getReader();
      readerRef.current = reader;

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log('Log stream completed');
          break;
        }
        const text = new TextDecoder().decode(value);
        console.log('Received log chunk:', text);
        setLogs(prevLogs => prevLogs + text);
      }
    } catch (error) {
      console.error('Error streaming logs:', error);
      setError('Failed to stream logs');
      throw error;
    }
  };

  const startPoemGeneration = async () => {
    if (!topic) return;

    try {
      setIsGenerating(true);
      setError(null);
      setLogs('');
      setShowModal(true);
      
      console.log('Creating flow execution...');
      const createResponse = await fetch('/api/flows/executions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          flow_name: 'poem',
          initial_state: {
            topic_title: topic.title,
            topic_description: topic.description
          }
        })
      });
      
      if (!createResponse.ok) {
        throw new Error(`Failed to create execution: ${createResponse.statusText}`);
      }

      const execution: FlowExecution = await createResponse.json();
      console.log(`Created execution with ID: ${execution.id}`);
      setExecutionId(execution.id);
      setStatus(execution.status);

      console.log('Starting flow execution...');
      const startResponse = await fetch(`/api/flows/executions/${execution.id}/start`, {
        method: 'POST'
      });

      if (!startResponse.ok) {
        throw new Error(`Failed to start execution: ${startResponse.statusText}`);
      }

      // Start streaming logs in a separate promise
      startLogStream(execution.id).catch(error => {
        console.error('Log streaming error:', error);
        setError('Failed to stream logs');
      });

    } catch (error) {
      console.error('Error generating poem:', error);
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
      setStatus('failed');
      setIsGenerating(false);
    }
  };

  const retryGeneration = () => {
    setError(null);
    setStatus(null);
    setExecutionId(null);
    startPoemGeneration();
  };

  const closeModal = () => {
    if (readerRef.current) {
      readerRef.current.cancel();
    }
    setShowModal(false);
    setIsGenerating(false);
    setError(null);
    setStatus(null);
    setExecutionId(null);
    setLogs('');
  };

  if (!topic) return null;

  return (
    <>
      <button
        onClick={startPoemGeneration}
        disabled={isGenerating}
        className={`inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 ${
          isGenerating ? 'opacity-50 cursor-not-allowed' : ''
        }`}
      >
        <PencilIcon className="w-5 h-5 mr-2" />
        {isGenerating ? 'Writing Poem...' : 'Write Poem'}
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-medium">Writing a Poem</h3>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-500"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            
            <div className="flex-1 overflow-auto p-4">
              {error ? (
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <p className="text-red-600">{error}</p>
                  <button
                    onClick={retryGeneration}
                    className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
                  >
                    Retry Generation
                  </button>
                </div>
              ) : (
                <>
                  <div className="mb-4">
                    <div className="flex items-center">
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className={`h-2.5 rounded-full ${
                            status === 'completed'
                              ? 'bg-green-600 w-full'
                              : status === 'failed'
                              ? 'bg-red-600'
                              : 'bg-blue-600 w-3/4 animate-pulse'
                          }`}
                        />
                      </div>
                      <span className="ml-2 text-sm text-gray-500">
                        {status || 'pending'}
                      </span>
                    </div>
                  </div>

                  <div className="bg-black text-green-400 font-mono text-sm rounded-md p-4 h-96 overflow-auto">
                    <pre>{logs || 'Initializing...'}</pre>
                    <div ref={logsEndRef} />
                  </div>
                </>
              )}
            </div>

            <div className="p-4 border-t">
              <button
                onClick={closeModal}
                className="w-full inline-flex justify-center items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
