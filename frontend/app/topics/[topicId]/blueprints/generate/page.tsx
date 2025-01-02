'use client'

import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { GenerateBlueprintDialog } from '@/components/blueprints/GenerateBlueprintDialog'
import { topicsApi } from '@/api/topics'

export default function GenerateBlueprintPage({ params }: { params: { topicId: string } }) {
  const router = useRouter()
  
  const { data: topic } = useQuery({
    queryKey: ['topic', params.topicId],
    queryFn: () => topicsApi.getTopic(params.topicId),
  })

  if (!topic) return null

  return (
    <GenerateBlueprintDialog
      topicId={params.topicId}
      isOpen={true}
      onClose={() => router.back()}
    />
  )
}
