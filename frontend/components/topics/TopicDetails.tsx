'use client'

import { useQuery } from '@tanstack/react-query';
import { PencilIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';
import { topicsApi } from '@/api/topics';
import { TopicContent } from './TopicContent';

interface Topic {
  topic_id: string;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
}

function formatDate(dateString: string | undefined) {
  console.log('Formatting date string:', dateString);
  if (!dateString) {
    console.warn('Date string is undefined');
    return 'Date not available';
  }
  
  try {
    const date = new Date(dateString);
    console.log('Parsed date object:', date);
    if (isNaN(date.getTime())) {
      console.warn('Invalid date parsed from:', dateString);
      return 'Invalid date';
    }
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    console.error('Error formatting date:', error, dateString);
    return 'Error formatting date';
  }
}

export function TopicDetails({ topicId }: { topicId: string }) {
  const { data: topic, isLoading, error } = useQuery<Topic>({
    queryKey: ['topic', topicId],
    queryFn: () => topicsApi.getTopic(topicId),
    retry: 1, // Only retry once
    staleTime: 30000, // Consider data fresh for 30 seconds
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (error) {
    console.error('Error fetching topic:', error);
    return (
      <div className="text-center py-8 text-red-500">
        <p>Error loading topic: {error instanceof Error ? error.message : 'Unknown error'}</p>
      </div>
    );
  }

  if (!topic) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Topic not found</p>
      </div>
    );
  }

  console.log('Rendering topic:', topic);

  const handleDelete = async () => {
    if (!topic) return;
    
    try {
      await topicsApi.deleteTopic(topic.topic_id);
      router.push('/topics');
    } catch (error) {
      console.error('Error deleting topic:', error);
      // TODO: Show error message to user
    }
  };

  return (
    <div>
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{topic.title}</h1>
          <p className="mt-2 text-gray-600">{topic.description}</p>
          <div className="mt-2 text-sm text-gray-500">
            <span>Created {formatDate(topic.created_at)}</span>
            <span className="mx-2">•</span>
            <span>Updated {formatDate(topic.updated_at)}</span>
          </div>
        </div>
        <Link
          href={`/topics/${topic.topic_id}/edit`}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          <PencilIcon className="w-5 h-5 mr-2" />
          Edit Topic
        </Link>
      </div>

      <TopicContent topicId={topic.topic_id} />
    </div>
  );
}
