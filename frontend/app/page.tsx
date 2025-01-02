import Link from 'next/link';

export default function Home() {
  return (
    <div className="space-y-8">
      <section className="text-center py-12">
        <h1 className="text-4xl font-bold mb-4">Welcome to QuizMaster Pro</h1>
        <p className="text-xl text-gray-600 mb-8">
          AI-Powered Assessment and Learning Platform
        </p>
        <Link 
          href="/topics/create"
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700"
        >
          Create New Topic
        </Link>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 border rounded-lg shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Topics</h2>
          <p className="text-gray-600 mb-4">Create and manage high-level subjects for assessment</p>
          <Link 
            href="/topics"
            className="text-blue-600 hover:underline"
          >
            View Topics →
          </Link>
        </div>

        <div className="p-6 border rounded-lg shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Assessment Blueprints</h2>
          <p className="text-gray-600 mb-4">Define learning objectives and generate questions</p>
          <Link 
            href="/blueprints"
            className="text-blue-600 hover:underline"
          >
            View Blueprints →
          </Link>
        </div>

        <div className="p-6 border rounded-lg shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Assessments</h2>
          <p className="text-gray-600 mb-4">Take assessments and track your progress</p>
          <Link 
            href="/assessments"
            className="text-blue-600 hover:underline"
          >
            View Assessments →
          </Link>
        </div>
      </section>
    </div>
  );
}
