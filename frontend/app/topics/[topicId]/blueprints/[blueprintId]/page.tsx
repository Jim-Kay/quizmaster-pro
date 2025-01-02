import { AssessmentsList } from '@/components/assessments/AssessmentsList';
import { BlueprintDetails } from '@/components/blueprints/BlueprintDetails';
import { Suspense } from 'react';

export default function BlueprintPage({ 
  params 
}: { 
  params: { id: string; blueprintId: string } 
}) {
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <Suspense fallback={<BlueprintDetailsSkeleton />}>
        <BlueprintDetails 
          topicId={params.id} 
          blueprintId={params.blueprintId} 
        />
      </Suspense>
      
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Assessments</h2>
        <Suspense fallback={<AssessmentsListSkeleton />}>
          <AssessmentsList 
            topicId={params.id} 
            blueprintId={params.blueprintId} 
          />
        </Suspense>
      </div>
    </div>
  );
}

function BlueprintDetailsSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-gray-200 rounded w-1/3"></div>
      <div className="h-4 bg-gray-200 rounded w-2/3"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
    </div>
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
