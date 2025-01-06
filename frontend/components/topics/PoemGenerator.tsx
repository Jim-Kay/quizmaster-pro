'use client'

import { useRef, useCallback, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSession } from 'next-auth/react';
import { Button, Icon, useDisclosure } from '@chakra-ui/react';
import { PencilIcon } from '@heroicons/react/24/outline';
import { topicsApi } from '../../api/topics';
import { useFlowExecution } from '../../hooks/useFlowExecution';
import { useLogStream } from '../../hooks/useLogStream';
import { PoemGeneratorModal } from './PoemGeneratorModal';

interface PoemGeneratorProps {
  topicId: string;
}

interface Topic {
  topic_id: string;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export function PoemGenerator({ topicId }: PoemGeneratorProps) {
  const { data: session } = useSession();
  const logsEndRef = useRef<HTMLDivElement>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [error, setError] = useState<string | null>(null);
  const lastPollTimeRef = useRef<number>(0);
  const POLL_INTERVAL = 5000; // 5 seconds between polls

  const { data: topic } = useQuery<Topic>({
    queryKey: ['topic', topicId],
    queryFn: () => topicsApi.getTopic(topicId),
    retry: 1,
    staleTime: 30000,
  });

  const {
    executionId,
    status,
    isGenerating,
    createExecution,
    startExecution,
    pollStatus
  } = useFlowExecution({
    onError: setError
  });

  const {
    logs,
    setLogs,
    startStream,
    stopStream
  } = useLogStream({
    onError: setError
  });

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Poll for status when execution is running
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (executionId && status !== 'completed' && status !== 'failed') {
      interval = setInterval(async () => {
        const now = Date.now();
        // Only poll if enough time has passed
        if (now - lastPollTimeRef.current >= POLL_INTERVAL) {
          lastPollTimeRef.current = now;
          await pollStatus();
        }
      }, POLL_INTERVAL);
    }
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [executionId, status, pollStatus]);

  const startGeneration = useCallback(async () => {
    if (!topic || !session?.accessToken || isGenerating) {
      console.log('Cannot start generation:', {
        hasTopic: !!topic,
        hasSession: !!session?.accessToken,
        isGenerating
      });
      return;
    }

    try {
      setError(null);
      setLogs('');
      onOpen();

      // Create execution
      const execution = await createExecution('poem', {
        topic_title: topic.title,
        topic_description: topic.description
      });

      if (!execution) {
        console.log('Failed to create execution or execution already in progress');
        setError('Failed to start poem generation. Please try again in a few seconds.');
        return;
      }

      // Start execution
      const started = await startExecution(execution.id);
      if (!started) {
        console.log('Failed to start execution');
        setError('Failed to start poem generation. Please try again.');
        return;
      }

      // Start log streaming
      try {
        await startStream(execution.id);
      } catch (error) {
        console.error('Error starting log stream:', error);
        setError('Failed to connect to log stream. The poem may still be generating.');
      }
    } catch (error) {
      console.error('Error generating poem:', error);
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
    }
  }, [topic, session?.accessToken, isGenerating, createExecution, startExecution, startStream, onOpen, setError]);

  const handleClose = useCallback(() => {
    stopStream();
    onClose();
    setError(null);
  }, [stopStream, onClose]);

  if (!topic) return null;

  return (
    <>
      <Button
        onClick={startGeneration}
        isDisabled={!session?.accessToken || isGenerating}
        colorScheme="purple"
        leftIcon={<Icon as={PencilIcon} boxSize={5} />}
        isLoading={isGenerating}
        loadingText="Writing Poem..."
        size="md"
        variant="solid"
        _hover={{ transform: 'translateY(-1px)' }}
        _active={{ transform: 'translateY(0)' }}
        transition="all 0.2s"
      >
        Write Poem
      </Button>

      <PoemGeneratorModal
        isOpen={isOpen}
        onClose={handleClose}
        logs={logs}
        error={error}
        status={status}
        onRetry={startGeneration}
        logsEndRef={logsEndRef}
      />
    </>
  );
}
