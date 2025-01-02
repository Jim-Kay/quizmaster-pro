'use client'

import { blueprintsApi } from '../../api/blueprints';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Blueprint, TerminalObjective, EnablingObjective } from '../../schemas/blueprint';
import { useState } from 'react';
import { PencilIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface BlueprintDetailsProps {
  topicId: string;
  blueprintId: string;
}

export function BlueprintDetails({ topicId, blueprintId }: BlueprintDetailsProps) {
  const queryClient = useQueryClient();
  const [editingTo, setEditingTo] = useState<string | null>(null);
  const [editingEo, setEditingEo] = useState<string | null>(null);
  const [editedTitle, setEditedTitle] = useState('');

  const { data: blueprint, isLoading, error } = useQuery<Blueprint>({
    queryKey: ['blueprint', topicId, blueprintId],
    queryFn: () => blueprintsApi.getBlueprint(topicId, blueprintId),
  });

  const updateMutation = useMutation({
    mutationFn: async ({ type, id, title }: { type: 'terminal' | 'enabling'; id: string; title: string }) => {
      if (!blueprint) return;
      
      const updatedBlueprint = { ...blueprint };
      if (type === 'terminal') {
        updatedBlueprint.terminal_objectives = blueprint.terminal_objectives.map(to =>
          to.terminal_objective_id === id ? { ...to, title } : to
        );
      } else {
        updatedBlueprint.terminal_objectives = blueprint.terminal_objectives.map(to => ({
          ...to,
          enabling_objectives: to.enabling_objectives.map(eo =>
            eo.enabling_objective_id === id ? { ...eo, title } : eo
          ),
        }));
      }
      
      return blueprintsApi.updateBlueprint(topicId, blueprintId, updatedBlueprint);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprint', topicId, blueprintId] });
      setEditingTo(null);
      setEditingEo(null);
      setEditedTitle('');
    },
  });

  const handleEdit = (type: 'terminal' | 'enabling', id: string, currentTitle: string) => {
    if (type === 'terminal') {
      setEditingTo(id);
    } else {
      setEditingEo(id);
    }
    setEditedTitle(currentTitle);
  };

  const handleSave = async (type: 'terminal' | 'enabling', id: string) => {
    await updateMutation.mutate({ type, id, title: editedTitle });
  };

  const handleCancel = () => {
    setEditingTo(null);
    setEditingEo(null);
    setEditedTitle('');
  };

  if (isLoading) return null;
  if (error) return <div>Error loading blueprint</div>;

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">{blueprint?.title}</h1>
      <div className="text-gray-600">
        <p>Status: {blueprint?.status}</p>
      </div>
      <div>
        <h2 className="text-xl font-semibold mb-2">Objectives</h2>
        <ul className="space-y-6">
          {blueprint?.terminal_objectives.map((to) => (
            <li key={to.terminal_objective_id} className="list-decimal group">
              <div className="flex items-center gap-2">
                {editingTo === to.terminal_objective_id ? (
                  <>
                    <input
                      type="text"
                      value={editedTitle}
                      onChange={(e) => setEditedTitle(e.target.value)}
                      className="flex-1 p-1 border rounded"
                      autoFocus
                    />
                    <button
                      onClick={() => handleSave('terminal', to.terminal_objective_id)}
                      className="p-1 text-green-600 hover:text-green-700"
                    >
                      <CheckIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={handleCancel}
                      className="p-1 text-red-600 hover:text-red-700"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </>
                ) : (
                  <>
                    <span>{to.title}</span>
                    <button
                      onClick={() => handleEdit('terminal', to.terminal_objective_id, to.title)}
                      className="p-1 opacity-0 group-hover:opacity-100 text-gray-600 hover:text-gray-800"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                  </>
                )}
              </div>
              {to.enabling_objectives.length > 0 && (
                <ul className="list-[circle] pl-8 mt-2 space-y-1">
                  {to.enabling_objectives.map((eo) => (
                    <li key={eo.enabling_objective_id} className="group">
                      <div className="flex items-center gap-2">
                        {editingEo === eo.enabling_objective_id ? (
                          <>
                            <input
                              type="text"
                              value={editedTitle}
                              onChange={(e) => setEditedTitle(e.target.value)}
                              className="flex-1 p-1 border rounded"
                              autoFocus
                            />
                            <button
                              onClick={() => handleSave('enabling', eo.enabling_objective_id)}
                              className="p-1 text-green-600 hover:text-green-700"
                            >
                              <CheckIcon className="h-5 w-5" />
                            </button>
                            <button
                              onClick={handleCancel}
                              className="p-1 text-red-600 hover:text-red-700"
                            >
                              <XMarkIcon className="h-5 w-5" />
                            </button>
                          </>
                        ) : (
                          <>
                            <span>{eo.title}</span>
                            <button
                              onClick={() => handleEdit('enabling', eo.enabling_objective_id, eo.title)}
                              className="p-1 opacity-0 group-hover:opacity-100 text-gray-600 hover:text-gray-800"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
