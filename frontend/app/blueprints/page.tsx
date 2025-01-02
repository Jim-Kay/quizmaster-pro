import Link from 'next/link';

const mockBlueprints = [
  {
    id: '1',
    title: 'React Fundamentals Blueprint',
    topic: 'React Fundamentals',
    terminalObjectives: 3,
    enablingObjectives: 8,
    createdAt: '2024-01-15',
  },
  {
    id: '2',
    title: 'Python Data Structures Blueprint',
    topic: 'Python Data Structures',
    terminalObjectives: 4,
    enablingObjectives: 12,
    createdAt: '2024-01-14',
  },
];

export default function BlueprintsPage() {
  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Assessment Blueprints</h1>
        <Link
          href="/topics"
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Create New Blueprint
        </Link>
      </div>

      <div className="space-y-6">
        {mockBlueprints.map((blueprint) => (
          <div key={blueprint.id} className="border rounded-lg p-6 shadow-sm">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-xl font-semibold mb-2">{blueprint.title}</h2>
                <p className="text-gray-600 mb-4">Topic: {blueprint.topic}</p>
                <div className="flex space-x-6 text-sm text-gray-500">
                  <div>
                    <span className="font-medium">{blueprint.terminalObjectives}</span> Terminal Objectives
                  </div>
                  <div>
                    <span className="font-medium">{blueprint.enablingObjectives}</span> Enabling Objectives
                  </div>
                  <div>Created: {blueprint.createdAt}</div>
                </div>
              </div>
              <div className="flex space-x-4">
                <Link
                  href={`/assessments/create?blueprintId=${blueprint.id}`}
                  className="text-blue-600 hover:underline"
                >
                  Generate Assessment
                </Link>
                <Link
                  href={`/blueprints/${blueprint.id}`}
                  className="text-blue-600 hover:underline"
                >
                  View Details
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
