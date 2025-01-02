'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { BookOpenIcon, PlusIcon, ChevronRightIcon, TrashIcon } from '@heroicons/react/24/outline';
import { Topic } from '@/schemas/topic';
import { topicsApi, UnauthorizedError, TopicNotFoundError } from '@/api/topics';

function formatDate(dateString: string | undefined) {
  if (!dateString) {
    return 'Date not available';
  }

  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      console.warn('Invalid date:', dateString);
      return 'Invalid date';
    }
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }).format(date);
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Error formatting date';
  }
}

export default function TopicsPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
      return;
    }

    if (status !== 'authenticated') {
      return;
    }

    const fetchTopics = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await topicsApi.getTopics();
        console.log('Fetched topics:', data);
        // Ensure dates are properly set
        const processedTopics = data.map(topic => ({
          ...topic,
          createdAt: topic.created_at,
          updatedAt: topic.updated_at
        }));
        setTopics(processedTopics);
      } catch (err) {
        console.error('Error fetching topics:', err);
        if (err instanceof UnauthorizedError) {
          router.push('/auth/signin');
        } else {
          setError('Failed to fetch topics');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchTopics();
  }, [router, status]);

  const handleDelete = async (topic_id?: string) => {
    if (!topic_id) {
      return;
    }

    if (!confirm('Are you sure you want to delete this topic?')) {
      return;
    }

    try {
      await topicsApi.deleteTopic(topic_id);
      setTopics(topics.filter(topic => topic.topic_id !== topic_id));
    } catch (err) {
      console.error('Error deleting topic:', err);
      if (err instanceof UnauthorizedError) {
        router.push('/auth/signin');
      } else if (err instanceof TopicNotFoundError) {
        setTopics(topics.filter(topic => topic.topic_id !== topic_id));
      } else {
        alert('Failed to delete topic');
      }
    }
  };

  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
        <div className="relative py-3 sm:max-w-xl sm:mx-auto">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-light-blue-500 shadow-lg transform -skew-y-6 sm:skew-y-0 sm:-rotate-6 sm:rounded-3xl"></div>
          <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
            <div className="max-w-md mx-auto">
              <div className="divide-y divide-gray-200">
                <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                  <p>Loading...</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-light-blue-500 shadow-lg transform -skew-y-6 sm:skew-y-0 sm:-rotate-6 sm:rounded-3xl"></div>
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <div className="max-w-md mx-auto">
            <div className="divide-y divide-gray-200">
              <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                <h1 className="text-2xl font-bold mb-4 flex items-center justify-between">
                  <span>Topics</span>
                  <Link href="/topics/new" className="inline-flex items-center justify-center p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors">
                    <PlusIcon className="h-5 w-5" />
                  </Link>
                </h1>
                {isLoading ? (
                  <p>Loading topics...</p>
                ) : error ? (
                  <p className="text-red-500">{error}</p>
                ) : topics.length === 0 ? (
                  <div className="text-center py-8">
                    <BookOpenIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-500">No topics found. Create your first topic!</p>
                  </div>
                ) : (
                  <ul className="space-y-4">
                    {topics.map(topic => (
                      <li key={topic.topic_id} className="group hover:bg-gray-50 p-3 rounded-lg transition-colors">
                        <div className="flex items-start space-x-3">
                          <BookOpenIcon className="h-6 w-6 text-blue-500 mt-1 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <div>
                                <h3 className="font-semibold text-gray-900 truncate">{topic.title}</h3>
                                <p className="text-sm text-gray-500 line-clamp-2">{topic.description}</p>
                                <p className="text-xs text-gray-400 mt-1">
                                  Created: {formatDate(topic.created_at)} • Updated: {formatDate(topic.updated_at)}
                                </p>
                              </div>
                              <div className="flex items-center space-x-2">
                                <button
                                  onClick={(e) => {
                                    e.preventDefault();
                                    if (topic.topic_id) {
                                      handleDelete(topic.topic_id);
                                    }
                                  }}
                                  className="p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                                  aria-label="Delete topic"
                                >
                                  <TrashIcon className="h-5 w-5" />
                                </button>
                                <Link
                                  href={`/topics/${topic.topic_id}`}
                                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                                  aria-label="View topic details"
                                >
                                  <ChevronRightIcon className="h-5 w-5" />
                                </Link>
                              </div>
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
                <div className="mt-4">
                  <Link
                    href="/topics/new"
                    className="inline-block bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                  >
                    Create New Topic
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
