'use client'

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { PlusIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface Assessment {
  id: string;
  title: string;
  status: 'draft' | 'in_progress' | 'completed';
  score?: number;
  questionCount: number;
  startedAt?: string;
  completedAt?: string;
}

export function AssessmentsList({ 
  topicId, 
  blueprintId 
}: { 
  topicId: string;
  blueprintId: string;
}) {
  const { data: assessments, isLoading } = useQuery<Assessment[]>({
    queryKey: ['assessments', blueprintId],
    queryFn: async () => {
      const response = await fetch(
        `/api/topics/${topicId}/blueprints/${blueprintId}/assessments`
      );
      if (!response.ok) {
        throw new Error('Failed to fetch assessments');
      }
      return response.json();
    },
  });

  if (isLoading) {
    return <AssessmentsListSkeleton />;
  }

  return (
    <div className="space-y-4">
      <Link
        href={`/topics/${topicId}/blueprints/${blueprintId}/assessments/create`}
        className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
      >
        <PlusIcon className="w-4 h-4 mr-2" />
        Start New Assessment
      </Link>

      <div className="grid gap-4">
        {assessments?.map((assessment) => (
          <Link
            key={assessment.id}
            href={`/topics/${topicId}/blueprints/${blueprintId}/assessments/${assessment.id}`}
            className="block p-4 border rounded-lg hover:border-blue-500 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center">
                  <h3 className="text-lg font-medium">{assessment.title}</h3>
                  <AssessmentStatusBadge status={assessment.status} />
                </div>
                <div className="flex items-center mt-2 text-sm text-gray-500">
                  <span>{assessment.questionCount} Questions</span>
                  {assessment.score !== undefined && (
                    <>
                      <span className="mx-2">•</span>
                      <span>Score: {assessment.score}%</span>
                    </>
                  )}
                  {assessment.startedAt && (
                    <>
                      <span className="mx-2">•</span>
                      <span>Started {new Date(assessment.startedAt).toLocaleDateString()}</span>
                    </>
                  )}
                  {assessment.completedAt && (
                    <>
                      <span className="mx-2">•</span>
                      <span>Completed {new Date(assessment.completedAt).toLocaleDateString()}</span>
                    </>
                  )}
                </div>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-400" />
            </div>
          </Link>
        ))}

        {assessments?.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No assessments yet. Start your first assessment to begin learning.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function AssessmentStatusBadge({ status }: { status: Assessment['status'] }) {
  const statusConfig = {
    draft: { color: 'bg-gray-100 text-gray-800', text: 'Draft' },
    in_progress: { color: 'bg-blue-100 text-blue-800', text: 'In Progress' },
    completed: { color: 'bg-green-100 text-green-800', text: 'Completed' },
  };

  const config = statusConfig[status];

  return (
    <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
      {config.text}
    </span>
  );
}

function AssessmentsListSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="p-4 border rounded-lg">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      ))}
    </div>
  );
}
