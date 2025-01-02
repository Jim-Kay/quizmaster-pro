'use client'

import { useQuery } from '@tanstack/react-query';
import { PencilIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';

interface Objective {
  id: string;
  title: string;
  description: string;
  type: 'terminal' | 'enabling';
  parent_id?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface Blueprint {
  id: string;
  title: string;
  description: string;
  topic_id: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  terminal_objectives_count: number;
  enabling_objectives_count: number;
  objectives: Objective[];
}

export function BlueprintDetails({ 
  topicId, 
  blueprintId 
}: { 
  topicId: string;
  blueprintId: string;
}) {
  const { data: blueprint, isLoading } = useQuery<Blueprint>({
    queryKey: ['blueprint', blueprintId],
    queryFn: async () => {
      const response = await fetch(`/api/topics/${topicId}/blueprints/${blueprintId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch blueprint');
      }
      return response.json();
    },
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

  if (!blueprint) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Blueprint not found</p>
      </div>
    );
  }

  const terminalObjectives = blueprint.objectives.filter(obj => obj.type === 'terminal');
  const enablingObjectives = blueprint.objectives.filter(obj => obj.type === 'enabling');

  return (
    <div>
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{blueprint.title}</h1>
          <p className="mt-2 text-gray-600">{blueprint.description}</p>
          <div className="mt-2 text-sm text-gray-500">
            <span>Created {new Date(blueprint.created_at).toLocaleDateString()}</span>
            <span className="mx-2">•</span>
            <span>Updated {new Date(blueprint.updated_at).toLocaleDateString()}</span>
          </div>
        </div>
        <Link
          href={`/topics/${topicId}/blueprints/${blueprintId}/edit`}
          className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          <PencilIcon className="w-4 h-4 mr-1" />
          Edit
        </Link>
      </div>

      <div className="mt-8 grid gap-8">
        <section>
          <h2 className="text-lg font-semibold mb-4">Terminal Objectives</h2>
          <div className="space-y-4">
            {terminalObjectives.map(objective => (
              <div key={objective.id} className="p-4 border rounded-lg">
                <h3 className="font-medium">{objective.title}</h3>
                <p className="mt-1 text-sm text-gray-600">{objective.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-4">Enabling Objectives</h2>
          <div className="space-y-4">
            {enablingObjectives.map(objective => (
              <div key={objective.id} className="p-4 border rounded-lg">
                <h3 className="font-medium">{objective.title}</h3>
                <p className="mt-1 text-sm text-gray-600">{objective.description}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
