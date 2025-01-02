import { Suspense } from 'react';
import { BlueprintDetails } from '@/components/blueprints/BlueprintDetails';

export default function BlueprintPage({ params }: { params: { topicId: string, blueprintId: string } }) {
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <Suspense fallback={<BlueprintDetailsSkeleton />}>
        <BlueprintDetails topicId={params.topicId} blueprintId={params.blueprintId} />
      </Suspense>
    </div>
  );
}

function BlueprintDetailsSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-gray-200 rounded w-1/3"></div>
      <div className="h-4 bg-gray-200 rounded w-2/3"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      <div className="h-4 bg-gray-200 rounded w-1/4"></div>
    </div>
  );
}
