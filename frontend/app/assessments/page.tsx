import Link from 'next/link';

const mockAssessments = [
  {
    id: '1',
    title: 'React Fundamentals Assessment',
    topic: 'React Fundamentals',
    totalQuestions: 20,
    completedAt: '2024-01-15',
    score: 85,
    timeSpent: '45 minutes',
  },
  {
    id: '2',
    title: 'Python Data Structures Assessment',
    topic: 'Python Data Structures',
    totalQuestions: 15,
    completedAt: null,
    score: null,
    timeSpent: null,
  },
];

export default function AssessmentsPage() {
  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Assessments</h1>
        <Link
          href="/blueprints"
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Generate New Assessment
        </Link>
      </div>

      <div className="space-y-6">
        {mockAssessments.map((assessment) => (
          <div key={assessment.id} className="border rounded-lg p-6 shadow-sm">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-xl font-semibold mb-2">{assessment.title}</h2>
                <p className="text-gray-600 mb-4">Topic: {assessment.topic}</p>
                <div className="flex space-x-6 text-sm text-gray-500">
                  <div>
                    <span className="font-medium">{assessment.totalQuestions}</span> Questions
                  </div>
                  {assessment.timeSpent && (
                    <div>Time Spent: {assessment.timeSpent}</div>
                  )}
                </div>
              </div>
              <div>
                {assessment.completedAt ? (
                  <div className="text-right">
                    <div className="text-2xl font-bold text-green-600">
                      {assessment.score}%
                    </div>
                    <div className="text-sm text-gray-500">
                      Completed {assessment.completedAt}
                    </div>
                    <Link
                      href={`/assessments/${assessment.id}/review`}
                      className="text-blue-600 hover:underline text-sm"
                    >
                      Review Assessment
                    </Link>
                  </div>
                ) : (
                  <Link
                    href={`/assessments/${assessment.id}/take`}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                  >
                    Start Assessment
                  </Link>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
