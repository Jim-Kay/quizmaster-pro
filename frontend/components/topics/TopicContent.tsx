'use client'

import { useState } from 'react';
import Link from 'next/link';
import { 
  BookOpenIcon, 
  PencilIcon, 
  DocumentTextIcon,
  PlusIcon,
  ChevronRightIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { BookGenerator } from './BookGenerator';
import { PoemGenerator } from './PoemGenerator';
import { useQuery, useQueryClient } from '@tanstack/react-query';

interface TopicContentProps {
  topicId: string;
}

type ContentType = 'blueprints' | 'books' | 'poems';

interface ContentTypeConfig {
  id: ContentType;
  name: string;
  icon: typeof BookOpenIcon;
  description: string;
}

interface Blueprint {
  blueprint_id: string;
  topic_id: string;
  title: string;
  description: string;
  created_at: string;
  terminal_objectives_count: number;
  enabling_objectives_count: number;
}

const contentTypes: ContentTypeConfig[] = [
  {
    id: 'blueprints',
    name: 'Assessment Blueprints',
    icon: DocumentTextIcon,
    description: 'Assessment blueprints for generating question sets'
  },
  {
    id: 'books',
    name: 'Books',
    icon: BookOpenIcon,
    description: 'Generate a comprehensive book about this topic'
  },
  {
    id: 'poems',
    name: 'Poems',
    icon: PencilIcon,
    description: 'Generate a creative poem about this topic'
  }
];

export function TopicContent({ topicId }: TopicContentProps) {
  const [selectedType, setSelectedType] = useState<ContentType>('blueprints');
  const queryClient = useQueryClient();

  // Fetch blueprints for this topic
  const { data: blueprints = [], isLoading: isLoadingBlueprints } = useQuery<Blueprint[]>({
    queryKey: ['blueprints', topicId],
    queryFn: () => fetch(`/api/topics/${topicId}/blueprints`).then(res => res.json()),
    retry: 1,
    staleTime: 30000,
  });

  const handleDeleteBlueprint = async (blueprintId: string) => {
    if (!confirm('Are you sure you want to delete this blueprint?')) {
      return;
    }
    
    try {
      await fetch(`/api/topics/${topicId}/blueprints/${blueprintId}`, {
        method: 'DELETE',
      });
      // Invalidate the blueprints query to refresh the list
      queryClient.invalidateQueries(['blueprints', topicId]);
    } catch (error) {
      console.error('Error deleting blueprint:', error);
      alert('Failed to delete blueprint');
    }
  };

  const renderBlueprintContent = () => {
    if (isLoadingBlueprints) {
      return (
        <div className="animate-pulse space-y-4">
          <div className="h-10 bg-gray-200 rounded w-full"></div>
          <div className="h-10 bg-gray-200 rounded w-full"></div>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900">Assessment Blueprints</h3>
          <button
            type="button"
            className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <PlusIcon className="-ml-0.5 mr-2 h-4 w-4" aria-hidden="true" />
            Create Blueprint
          </button>
        </div>

        {blueprints.length === 0 ? (
          <div className="text-center py-6">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No blueprints</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating an assessment blueprint.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {blueprints.map((blueprint) => (
              <div 
                key={blueprint.blueprint_id}
                className="bg-white rounded-lg border border-gray-200 p-4 hover:border-gray-300"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <Link 
                        href={`/topics/${topicId}/blueprints/${blueprint.blueprint_id}`}
                        className="text-sm font-medium text-indigo-600 hover:text-indigo-500 truncate"
                      >
                        {blueprint.title}
                      </Link>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Active
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      {blueprint.description}
                    </p>
                    <div className="mt-2 flex items-center text-xs text-gray-500">
                      <span>{blueprint.terminal_objectives_count} Terminal Objectives</span>
                      <span className="mx-2">•</span>
                      <span>{blueprint.enabling_objectives_count} Enabling Objectives</span>
                      <span className="mx-2">•</span>
                      <span>Created {new Date(blueprint.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="ml-4 flex items-center space-x-2">
                    <button
                      type="button"
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Generate Assessment Set
                    </button>
                    <Link
                      href={`/topics/${topicId}/blueprints/${blueprint.blueprint_id}`}
                      className="p-1.5 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      <ChevronRightIcon className="h-5 w-5" aria-hidden="true" />
                    </Link>
                    <button
                      onClick={() => handleDeleteBlueprint(blueprint.blueprint_id)}
                      className="p-1.5 text-gray-400 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >
                      <TrashIcon className="h-5 w-5" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderContent = () => {
    switch (selectedType) {
      case 'blueprints':
        return renderBlueprintContent();
      case 'books':
        return (
          <div className="space-y-4">
            <div className="text-sm text-gray-500">
              Generate a comprehensive book about this topic.
            </div>
            <BookGenerator topicId={topicId} />
          </div>
        );
      case 'poems':
        return (
          <div className="space-y-4">
            <div className="text-sm text-gray-500">
              Generate a creative poem about this topic.
            </div>
            <PoemGenerator topicId={topicId} />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="mt-6">
      <div className="sm:hidden">
        <label htmlFor="content-type" className="sr-only">
          Select content type
        </label>
        <select
          id="content-type"
          name="content-type"
          className="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value as ContentType)}
        >
          {contentTypes.map((type) => (
            <option key={type.id} value={type.id}>
              {type.name}
            </option>
          ))}
        </select>
      </div>
      <div className="hidden sm:block">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8" aria-label="Content types">
            {contentTypes.map((type) => {
              const Icon = type.icon;
              return (
                <button
                  key={type.id}
                  onClick={() => setSelectedType(type.id)}
                  className={`
                    ${
                      selectedType === type.id
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }
                    whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium flex items-center
                  `}
                >
                  <Icon
                    className={`
                      ${
                        selectedType === type.id
                          ? 'text-indigo-500'
                          : 'text-gray-400 group-hover:text-gray-500'
                      }
                      -ml-0.5 mr-2 h-5 w-5
                    `}
                    aria-hidden="true"
                  />
                  {type.name}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="mt-6">
        <div className="px-4 py-5">
          {selectedType === 'blueprints' ? renderBlueprintContent() : 
            selectedType === 'books' ? (
              <div className="space-y-4">
                <div className="text-sm text-gray-500">
                  Generate a comprehensive book about this topic.
                </div>
                <BookGenerator topicId={topicId} />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-sm text-gray-500">
                  Generate a creative poem about this topic.
                </div>
                <PoemGenerator topicId={topicId} />
              </div>
            )
          }
        </div>
      </div>
    </div>
  );
}
