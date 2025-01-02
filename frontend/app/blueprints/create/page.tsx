'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface TerminalObjective {
  number: number;
  description: string;
  cognitiveLevel: string;
  enablingObjectives: {
    number: string;
    description: string;
    cognitiveLevel: string;
  }[];
}

const cognitiveLevels = [
  'remember',
  'understand',
  'apply',
  'analyze',
  'evaluate',
  'create',
];

export default function CreateBlueprintPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const topicId = searchParams.get('topicId');

  const [terminalObjectives, setTerminalObjectives] = useState<TerminalObjective[]>([
    {
      number: 1,
      description: '',
      cognitiveLevel: 'understand',
      enablingObjectives: [],
    },
  ]);

  const addTerminalObjective = () => {
    if (terminalObjectives.length < 10) {
      setTerminalObjectives([
        ...terminalObjectives,
        {
          number: terminalObjectives.length + 1,
          description: '',
          cognitiveLevel: 'understand',
          enablingObjectives: [],
        },
      ]);
    }
  };

  const addEnablingObjective = (terminalIndex: number) => {
    const updatedObjectives = [...terminalObjectives];
    const terminalObj = updatedObjectives[terminalIndex];
    
    if (terminalObj.enablingObjectives.length < 8) {
      terminalObj.enablingObjectives.push({
        number: `${terminalObj.number}.${terminalObj.enablingObjectives.length + 1}`,
        description: '',
        cognitiveLevel: 'understand',
      });
      setTerminalObjectives(updatedObjectives);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement API call to create blueprint
    console.log('Creating blueprint:', { topicId, terminalObjectives });
    router.push('/blueprints');
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Create Assessment Blueprint</h1>

      <form onSubmit={handleSubmit} className="space-y-8">
        {terminalObjectives.map((terminal, tIndex) => (
          <div key={tIndex} className="border rounded-lg p-6 space-y-4">
            <h2 className="text-xl font-semibold">Terminal Objective {terminal.number}</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={terminal.description}
                  onChange={(e) => {
                    const updated = [...terminalObjectives];
                    updated[tIndex].description = e.target.value;
                    setTerminalObjectives(updated);
                  }}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  rows={3}
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Cognitive Level</label>
                <select
                  value={terminal.cognitiveLevel}
                  onChange={(e) => {
                    const updated = [...terminalObjectives];
                    updated[tIndex].cognitiveLevel = e.target.value;
                    setTerminalObjectives(updated);
                  }}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {cognitiveLevels.map((level) => (
                    <option key={level} value={level}>
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">Enabling Objectives</h3>
                <button
                  type="button"
                  onClick={() => addEnablingObjective(tIndex)}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  Add Enabling Objective
                </button>
              </div>

              {terminal.enablingObjectives.map((enabling, eIndex) => (
                <div key={eIndex} className="ml-6 p-4 border rounded bg-gray-50">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Description ({enabling.number})
                      </label>
                      <textarea
                        value={enabling.description}
                        onChange={(e) => {
                          const updated = [...terminalObjectives];
                          updated[tIndex].enablingObjectives[eIndex].description = e.target.value;
                          setTerminalObjectives(updated);
                        }}
                        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        rows={2}
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Cognitive Level</label>
                      <select
                        value={enabling.cognitiveLevel}
                        onChange={(e) => {
                          const updated = [...terminalObjectives];
                          updated[tIndex].enablingObjectives[eIndex].cognitiveLevel = e.target.value;
                          setTerminalObjectives(updated);
                        }}
                        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        {cognitiveLevels.map((level) => (
                          <option key={level} value={level}>
                            {level.charAt(0).toUpperCase() + level.slice(1)}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        <div className="flex justify-between">
          <button
            type="button"
            onClick={addTerminalObjective}
            className="text-blue-600 hover:text-blue-700"
          >
            Add Terminal Objective
          </button>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Create Blueprint
          </button>
        </div>
      </form>
    </div>
  );
}
