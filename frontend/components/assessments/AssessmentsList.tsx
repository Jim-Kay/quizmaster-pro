'use client'

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { PlusIcon } from '@heroicons/react/24/outline';
import { assessmentsApi } from '../../api/assessments';

export function AssessmentsList({ 
  topicId, 
  blueprintId 
}: { 
  topicId: string;
  blueprintId: string;
}) {
  const { data: assessmentCount, isLoading } = useQuery<number>({
    queryKey: ['assessmentCount', blueprintId],
    queryFn: () => assessmentsApi.getAssessmentCount(topicId, blueprintId),
  });

  if (isLoading) {
    return <AssessmentsListSkeleton />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-gray-600">
            {assessmentCount === 0 ? 'No assessments yet' : `${assessmentCount} assessment${assessmentCount === 1 ? '' : 's'}`}
          </span>
        </div>
        <Link
          href={`/topics/${topicId}/blueprints/${blueprintId}/assessments/create`}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          Start New Assessment
        </Link>
      </div>

      {assessmentCount === 0 && (
        <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg">
          <p>Start your first assessment to begin learning.</p>
        </div>
      )}
    </div>
  );
}

function AssessmentsListSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="flex items-center justify-between">
        <div className="h-6 bg-gray-200 rounded w-24"></div>
        <div className="h-10 bg-gray-200 rounded w-40"></div>
      </div>
      <div className="h-32 bg-gray-200 rounded"></div>
    </div>
  );
}
