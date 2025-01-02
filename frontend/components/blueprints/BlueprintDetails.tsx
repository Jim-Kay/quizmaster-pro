'use client'

import { blueprintsApi } from '@/api/blueprints';
import { useQuery } from '@tanstack/react-query';
import type { Blueprint } from '@/schemas/blueprint';

interface BlueprintDetailsProps {
  topicId: string;
  blueprintId: string;
}

export function BlueprintDetails({ topicId, blueprintId }: BlueprintDetailsProps) {
  const { data: blueprint, isLoading, error } = useQuery<Blueprint>({
    queryKey: ['blueprint', topicId, blueprintId],
    queryFn: () => blueprintsApi.getBlueprint(topicId, blueprintId),
  });

  if (isLoading) return null;
  if (error) return <div>Error loading blueprint</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">{blueprint?.title}</h1>
      <div className="text-gray-600">
        <p>Status: {blueprint?.status}</p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h2 className="text-xl font-semibold mb-2">Terminal Objectives</h2>
          <ul className="list-disc pl-5">
            {blueprint?.terminal_objectives.map((obj) => (
              <li key={obj.terminal_objective_id}>{obj.title}</li>
            ))}
          </ul>
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-2">Enabling Objectives</h2>
          <ul className="list-disc pl-5">
            {blueprint?.terminal_objectives.flatMap(to => 
              to.enabling_objectives.map((eo) => (
                <li key={eo.enabling_objective_id}>{eo.title}</li>
              ))
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
