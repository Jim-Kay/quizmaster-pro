'use client';

import { useQuery } from '@tanstack/react-query';
import { EditTopicForm } from '@/components/topics/EditTopicForm';
import { useRouter } from 'next/navigation';
import { topicsApi } from '@/api/topics';

interface EditTopicPageProps {
  params: {
    topicId: string;
  };
}

export default function EditTopicPage({ params }: EditTopicPageProps) {
  const router = useRouter();

  const { data: topic, isLoading, error } = useQuery({
    queryKey: ['topic', params.topicId],
    queryFn: () => topicsApi.getTopic(params.topicId),
  });

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-red-50 p-4 rounded-md">
          <h3 className="text-sm font-medium text-red-800">Error</h3>
          <div className="mt-2 text-sm text-red-700">
            Failed to load topic. Please try again later.
          </div>
        </div>
      </div>
    );
  }

  if (!topic) {
    return null;
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Edit Topic</h1>
      <EditTopicForm
        topicId={params.topicId}
        initialData={{
          title: topic.title,
          description: topic.description,
        }}
      />
    </div>
  );
}
