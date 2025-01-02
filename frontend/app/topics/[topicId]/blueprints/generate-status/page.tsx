'use client'

import { useSearchParams } from 'next/navigation'
import { BlueprintGenerationContent } from '../generate/content'

export default function BlueprintGenerationStatusPage({ params }: { params: { topicId: string } }) {
  const searchParams = useSearchParams()
  const blueprintId = searchParams.get('blueprintId')

  if (!blueprintId) {
    return <div>No blueprint ID provided</div>
  }

  return <BlueprintGenerationContent initialBlueprintId={blueprintId} />
}
