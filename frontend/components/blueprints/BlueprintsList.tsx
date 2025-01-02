'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import {
  Box,
  Button,
  Flex,
  Heading,
  Icon,
  List,
  ListItem,
  Text,
  useToast,
  VStack,
} from '@chakra-ui/react';
import { DocumentIcon, PlusIcon, ChevronRightIcon, TrashIcon } from '@heroicons/react/24/outline';
import { blueprintsApi, UnauthorizedError, BlueprintNotFoundError } from '@/api/blueprints';
import { topicsApi } from '@/api/topics';

interface Blueprint {
  blueprint_id: string;
  title: string;
  description: string;
  terminal_objectives_count: number;
  enabling_objectives_count: number;
  created_at: string;
  updated_at: string;
}

interface BlueprintCount {
  count: number;
}

interface Topic {
  topic_id: string;
  title: string;
  description: string;
}

export function BlueprintsList({ topicId }: { topicId: string }) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: topic } = useQuery<Topic>({
    queryKey: ['topic', topicId],
    queryFn: () => topicsApi.getTopic(topicId),
  });

  const { data: blueprints = [], isLoading, error } = useQuery<Blueprint[]>({
    queryKey: ['blueprints', topicId],
    queryFn: () => blueprintsApi.getBlueprints(topicId),
  });

  const { data: blueprintCount } = useQuery<BlueprintCount>({
    queryKey: ['blueprintCount', topicId],
    queryFn: async () => {
      const count = await blueprintsApi.getBlueprintCount(topicId);
      return { count };
    },
  });

  const deleteBlueprintMutation = useMutation({
    mutationFn: (blueprintId: string) => blueprintsApi.deleteBlueprint(topicId, blueprintId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blueprints', topicId] });
      queryClient.invalidateQueries({ queryKey: ['blueprintCount', topicId] });
      toast({
        title: 'Blueprint deleted',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    },
    onError: (error) => {
      console.error('Error deleting blueprint:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete blueprint',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const handleDelete = async (e: React.MouseEvent, blueprintId: string) => {
    e.preventDefault(); // Prevent the link from being followed
    console.log('Deleting blueprint with ID:', blueprintId);
    if (window.confirm('Are you sure you want to delete this blueprint?')) {
      try {
        await deleteBlueprintMutation.mutateAsync(blueprintId);
      } catch (error) {
        console.error('Error deleting blueprint:', error);
      }
    }
  };

  if (isLoading) {
    return (
      <Box p={4}>
        <Text>Loading blueprints...</Text>
      </Box>
    );
  }

  if (error) {
    console.error('Error in BlueprintsList:', error);
    return (
      <Box p={4}>
        <Text color="red.500">Error loading blueprints</Text>
      </Box>
    );
  }

  console.log('Rendering blueprints:', blueprints);
  const hasBlueprints = blueprints && blueprints.length > 0;

  return (
    <Box bg="white" shadow="sm" rounded="lg" p={6}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="md">Blueprints</Heading>
        <Button
          as={Link}
          href={`/topics/${topicId}/blueprints/generate`}
          leftIcon={<Icon as={PlusIcon} />}
          colorScheme="blue"
          size="sm"
        >
          Generate New
        </Button>
      </Flex>

      {!hasBlueprints ? (
        <Box textAlign="center" py={8}>
          <Icon as={DocumentIcon} w={12} h={12} color="gray.400" mb={4} />
          <Text color="gray.500">No blueprints found. Generate your first blueprint!</Text>
        </Box>
      ) : (
        <List spacing={4}>
          {blueprints.map((blueprint) => (
            <ListItem
              key={blueprint.blueprint_id}
              p={4}
              border="1px"
              borderColor="gray.200"
              rounded="md"
              _hover={{ bg: 'gray.50' }}
            >
              <Flex justify="space-between" align="start">
                <Box flex={1}>
                  <Flex align="center" mb={2}>
                    <Icon as={DocumentIcon} w={5} h={5} color="blue.500" mr={2} />
                    <Text fontWeight="semibold">{blueprint.title || 'Untitled Blueprint'}</Text>
                  </Flex>
                  <Text color="gray.600" fontSize="sm" mb={2}>
                    {blueprint.description || 'No description'}
                  </Text>
                  <Flex gap={4}>
                    <Text fontSize="sm" color="gray.500">
                      {blueprint.terminal_objectives_count || 0} Terminal Objectives
                    </Text>
                    <Text fontSize="sm" color="gray.500">
                      {blueprint.enabling_objectives_count || 0} Enabling Objectives
                    </Text>
                  </Flex>
                </Box>
                <Flex gap={2}>
                  <Button
                    size="sm"
                    variant="ghost"
                    colorScheme="red"
                    onClick={(e) => handleDelete(e, blueprint.blueprint_id)}
                  >
                    <Icon as={TrashIcon} w={4} h={4} />
                  </Button>
                  <Button
                    as={Link}
                    href={`/topics/${topicId}/blueprints/${blueprint.blueprint_id}`}
                    size="sm"
                    variant="ghost"
                  >
                    <Icon as={ChevronRightIcon} w={4} h={4} />
                  </Button>
                </Flex>
              </Flex>
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
}
