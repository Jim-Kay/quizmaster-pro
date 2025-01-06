'use client'

import { useState, useEffect, useRef } from 'react';
import { BookOpenIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { useSession } from 'next-auth/react';
import { topicsApi } from '@/api/topics';

interface BookGeneratorProps {
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

export function BookGenerator({ topicId }: BookGeneratorProps) {
  const { data: session } = useSession();
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

  // Poll for status updates
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (executionId && status && status !== 'completed' && status !== 'failed') {
      interval = setInterval(async () => {
        try {
          console.log(`Polling status for execution ${executionId}...`);
          const response = await fetch(`/api/flows/executions/${executionId}`, {
            headers: {
              'Authorization': `Bearer ${session?.accessToken}`
            }
          });
          if (response.status === 401) {
            setError('Unauthorized. Please sign in again.');
            clearInterval(interval);
            setIsGenerating(false);
            return;
          }
          const execution: FlowExecution = await response.json();
          console.log(`Current status: ${execution.status}`);
          setStatus(execution.status);
          if (execution.status === 'completed' || execution.status === 'failed') {
            clearInterval(interval);
            setIsGenerating(false);
          }
        } catch (error) {
          console.error('Error polling status:', error);
          clearInterval(interval);
          setIsGenerating(false);
          setError('Failed to get status updates');
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [executionId, status, session?.accessToken]);

  const startLogStream = async (executionId: string) => {
    try {
      console.log('Starting log stream...');
      const logsResponse = await fetch(`/api/flows/executions/${executionId}/logs`, {
        headers: {
          'Authorization': `Bearer ${session?.accessToken}`
        }
      });
      
      if (logsResponse.status === 401) {
        throw new Error('Unauthorized. Please sign in again.');
      }

      if (!logsResponse.ok) {
        throw new Error(`Failed to fetch logs: ${logsResponse.statusText}`);
      }

      const reader = logsResponse.body?.getReader();
      if (!reader) {
        throw new Error('No reader available');
      }
      readerRef.current = reader;

      const decoder = new TextDecoder();
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        setLogs(prevLogs => prevLogs + text);
      }
    } catch (error) {
      console.error('Error streaming logs:', error);
      throw error;
    }
  };

  const startBookGeneration = async () => {
    if (!topic || !session?.accessToken) return;

    try {
      setIsGenerating(true);
      setError(null);
      setLogs('');
      setShowModal(true);
      
      console.log('Creating flow execution...');
      try {
        const createResponse = await fetch('/api/flows/executions', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.accessToken}`
          },
          body: JSON.stringify({
            flow_name: 'poem',
            initial_state: {
              topic_title: topic.title,
              topic_description: topic.description
            },
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
        console.log('Flow execution created:', data);
        const execution: FlowExecution = data;
        console.log(`Created execution with ID: ${execution.id}`);
        setExecutionId(execution.id);
        setStatus(execution.status);

        console.log('Starting flow execution...');
        const startResponse = await fetch(`/api/flows/executions/${execution.id}/start`, {
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

        // Start log streaming after flow execution has started
        console.log('Starting log stream...');
        await startLogStream(execution.id).catch(error => {
          console.error('Log streaming error:', error);
          setError('Failed to stream logs');
        });

      } catch (error) {
        console.error('Error creating flow:', error);
        throw error;
      }

    } catch (error) {
      console.error('Error generating book:', error);
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
      setIsGenerating(false);
    }
  };

  const retryGeneration = () => {
    setError(null);
    setStatus(null);
    setExecutionId(null);
    startBookGeneration();
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

  const downloadBook = async () => {
    if (!executionId) return;
    
    try {
      console.log('Attempting to download book...');
      alert('Book download not yet implemented');
    } catch (error) {
      console.error('Error downloading book:', error);
      setError('Failed to download book');
    }
  };

  if (!topic) return null;

  return (
    <>
      <button
        onClick={startBookGeneration}
        disabled={isGenerating || !session?.accessToken}
        className={`inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 ${
          (isGenerating || !session?.accessToken) ? 'opacity-50 cursor-not-allowed' : ''
        }`}
      >
        <BookOpenIcon className="w-5 h-5 mr-2" />
        Generate Book
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-medium">Generating Book</h3>
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
              {status === 'completed' ? (
                <button
                  onClick={downloadBook}
                  className="w-full inline-flex justify-center items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700"
                >
                  Download Book
                </button>
              ) : (
                <button
                  onClick={closeModal}
                  className="w-full inline-flex justify-center items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Close
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
