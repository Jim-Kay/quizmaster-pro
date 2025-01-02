'use client'

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { PlusIcon } from '@heroicons/react/24/outline';

interface Topic {
  topic_id: string;
  title: string;
  description: string;
}

export function TopicsSidebar() {
  const pathname = usePathname();
  
  const { data: topics, isLoading } = useQuery<Topic[]>({
    queryKey: ['topics'],
    queryFn: async () => {
      const response = await fetch('/api/topics');
      if (!response.ok) {
        throw new Error('Failed to fetch topics');
      }
      return response.json();
    },
  });

  if (isLoading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-8 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-200">
        <Link
          href="/topics/create"
          className="flex items-center justify-center w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          New Topic
        </Link>
      </div>
      
      <div className="flex-1 overflow-y-auto p-2">
        {topics?.map((topic) => (
          <Link
            key={topic.topic_id}
            href={`/topics/${topic.topic_id}`}
            className={`block px-3 py-2 mb-1 rounded-md text-sm ${
              pathname.includes(topic.topic_id)
                ? 'bg-blue-50 text-blue-700'
                : 'hover:bg-gray-100'
            }`}
          >
            {topic.title}
          </Link>
        ))}
      </div>
    </div>
  );
}
