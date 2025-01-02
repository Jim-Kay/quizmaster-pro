'use client'

import { CreateBlueprintForm } from '@/components/blueprints/CreateBlueprintForm';
import { Suspense } from 'react';

interface CreateBlueprintPageProps {
  params: {
    id: string;
  };
}

export default function CreateBlueprintPage({ params }: CreateBlueprintPageProps) {
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Create Assessment Blueprint</h1>
      <Suspense fallback={<div>Loading...</div>}>
        <CreateBlueprintForm topicId={params.id} />
      </Suspense>
    </div>
  );
}
