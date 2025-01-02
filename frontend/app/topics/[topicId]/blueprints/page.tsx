'use client';

import { useParams } from 'next/navigation';
import { BlueprintsList } from '@/components/blueprints/BlueprintsList';
import { PageHeader } from '@/components/common/PageHeader';

export default function TopicBlueprintsPage() {
  const params = useParams();
  const topicId = params.topicId as string;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Assessment Blueprints"
        description="Create and manage assessment blueprints for this topic"
      />
      <BlueprintsList topicId={topicId} />
    </div>
  );
}
