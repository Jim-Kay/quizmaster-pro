'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { SparklesIcon } from '@heroicons/react/24/outline'
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
  Button,
  Text,
  useToast,
  VStack,
  Icon,
} from '@chakra-ui/react'

interface GenerateBlueprintDialogProps {
  topicId: string
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
}

export function GenerateBlueprintDialog({
  topicId,
  isOpen,
  onClose,
  onSuccess,
}: GenerateBlueprintDialogProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const router = useRouter()
  const queryClient = useQueryClient()
  const toast = useToast()

  const generateMutation = useMutation({
    mutationFn: async () => {
      console.log('Starting blueprint generation for topic:', topicId)
      const response = await fetch(`/api/topics/${topicId}/blueprints/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      })

      if (!response.ok) {
        const error = await response.json()
        console.error('Blueprint generation failed:', error)
        throw new Error(error.message || 'Failed to generate blueprint')
      }

      return response.json()
    },
    onSuccess: (data) => {
      console.log('Blueprint generation successful:', data)
      queryClient.invalidateQueries({ queryKey: ['blueprints', topicId] })
      toast({
        title: 'Success',
        description: 'Blueprint generation started',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
      onSuccess?.()
    },
    onError: (error) => {
      console.error('Blueprint generation error:', error)
      toast({
        title: 'Error',
        description: 'Failed to start blueprint generation',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    },
  })

  const handleGenerate = async () => {
    setIsGenerating(true)
    try {
      const result = await generateMutation.mutateAsync()
      if (result?.blueprint_id) {
        router.push(`/topics/${topicId}/blueprints/generate-status?blueprintId=${result.blueprint_id}`)
      } else {
        throw new Error('No blueprint ID received from generation')
      }
    } catch (error) {
      console.error('Error in handleGenerate:', error)
      toast({
        title: 'Error',
        description: 'Failed to start blueprint generation',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
      onClose()
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      isCentered
      motionPreset="slideInBottom"
    >
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Generate Blueprint</ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <VStack spacing={4} align="stretch">
            <Text>
              Would you like to generate a new assessment blueprint? This will create a comprehensive set of learning objectives based on the topic content.
            </Text>
          </VStack>
        </ModalBody>

        <ModalFooter gap={3}>
          <Button
            variant="ghost"
            onClick={onClose}
            isDisabled={isGenerating}
          >
            Cancel
          </Button>
          <Button
            colorScheme="blue"
            onClick={handleGenerate}
            isLoading={isGenerating}
            loadingText="Generating..."
            leftIcon={<Icon as={SparklesIcon} />}
          >
            Generate
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}
