import { BlueprintsList } from '@/components/blueprints/BlueprintsList';
import { TopicDetails } from '@/components/topics/TopicDetails';
import { BookGenerator } from '@/components/topics/BookGenerator';
import { Suspense } from 'react';

export default function TopicPage({ params }: { params: { topicId: string } }) {
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <Suspense fallback={<TopicDetailsSkeleton />}>
        <TopicDetails topicId={params.topicId} />
      </Suspense>
    </div>
  );
}

function TopicDetailsSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-gray-200 rounded w-1/3"></div>
      <div className="h-4 bg-gray-200 rounded w-2/3"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
    </div>
  );
}

function BlueprintsListSkeleton() {
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
