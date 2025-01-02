'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
    Card,
    CardBody,
    Button,
    Progress,
    Text,
    VStack,
    HStack,
    Heading,
    useToast,
    Spinner,
} from '@chakra-ui/react';
import { BlueprintStatus } from '@/src/types/blueprint';
import { useQueryClient } from '@tanstack/react-query';

const POLL_INTERVAL = 5000; // 5 seconds
const MAX_RETRIES = 100;
const RETRY_DELAY = 5000; // Constant 5 second delay between retries

const calculateProgress = (status: BlueprintStatus | null): number => {
    if (!status) return 0;
    
    switch (status.status) {
        case 'completed':
        case 'published':
            return 100;
        case 'error':
        case 'archived':
            return 0;
        case 'draft':
            return 5;
        case 'generating':
            // Calculate progress based on objectives count
            const targetTerminalObjectives = 10; // Expected number of terminal objectives
            const progress = (status.terminal_objectives_count / targetTerminalObjectives) * 100;
            return Math.min(Math.max(progress, 5), 90); // Keep between 5% and 90%
        default:
            return 0;
    }
};

interface BlueprintGenerationContentProps {
    initialBlueprintId?: string;
}

export function BlueprintGenerationContent({ initialBlueprintId }: BlueprintGenerationContentProps) {
    const params = useParams();
    const router = useRouter();
    const toast = useToast();
    const queryClient = useQueryClient();
    const [status, setStatus] = useState<BlueprintStatus | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [blueprintId, setBlueprintId] = useState<string | null>(initialBlueprintId || null);

    const topicId = params.topicId as string;

    useEffect(() => {
        if (initialBlueprintId) {
            console.log('🔄 Starting polling for existing blueprint:', initialBlueprintId);
            setBlueprintId(initialBlueprintId);
            setIsGenerating(true);
        }
        return () => {
            console.log('⏹️ Cleaning up - stopping polling');
            setIsGenerating(false);
            setBlueprintId(null);
        };
    }, [initialBlueprintId]);

    useEffect(() => {
        if (isGenerating && blueprintId) {
            console.log('🔄 Starting polling for blueprint:', blueprintId);
            pollStatus(blueprintId, 0);
        }
    }, [isGenerating, blueprintId]);

    const startGeneration = async () => {
        console.log('🚀 Starting blueprint generation for topic:', topicId);
        setIsGenerating(true);
        try {
            console.log('📡 Making POST request to generate blueprint...');
            const response = await fetch(`/api/topics/${topicId}/blueprints/generate`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error(`Failed to start blueprint generation: ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ Generation response:', data);
            
            // Check if this is an existing generation process
            if (data.status === "generating" && data.terminal_objectives_count > 0) {
                console.log('📝 Continuing existing generation process');
                toast({
                    title: 'Generation In Progress',
                    description: 'This blueprint is already being generated. Showing current progress...',
                    status: 'info',
                    duration: 5000,
                    isClosable: true,
                });
            } else {
                console.log('🆕 Starting new generation process');
            }
            
            setBlueprintId(data.id);
            setStatus(data);
            pollStatus(data.id);
        } catch (error) {
            console.error('❌ Generation error:', error);
            toast({
                title: 'Error',
                description: 'Failed to start blueprint generation. Please try again.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
            setIsGenerating(false);
        }
    };

    const pollStatus = async (blueprintId: string, retryCount = 0) => {
        if (!isGenerating || !blueprintId) {
            console.log('⏹️ Polling stopped - generation inactive or no blueprint ID');
            return;
        }

        try {
            console.log(`📊 Polling status for blueprint: ${blueprintId} (attempt ${retryCount + 1})`);
            const response = await fetch(`/api/topics/${topicId}/blueprints/${encodeURIComponent(blueprintId)}/status`, {
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            if (!response.ok) {
                throw new Error(`Failed to fetch blueprint status: ${response.status}`);
            }

            const data = await response.json();
            console.log('📈 Status update:', {
                status: data.status,
                terminal_objectives: data.terminal_objectives_count,
                enabling_objectives: data.enabling_objectives_count,
            });

            setStatus(data);

            if (data.status === 'completed') {
                console.log('✨ Generation completed successfully!');
                setIsGenerating(false);
                toast({
                    title: 'Success',
                    description: 'Blueprint generation completed!',
                    status: 'success',
                    duration: 5000,
                    isClosable: true,
                });
                queryClient.invalidateQueries({ queryKey: ['blueprints', topicId] });
                router.push(`/topics/${topicId}/blueprints/${blueprintId}`);
            } else if (data.status === 'error' || data.error) {
                console.log('❌ Generation failed:', data.error || 'Unknown error');
                setIsGenerating(false);
                toast({
                    title: 'Error',
                    description: data.error || 'Blueprint generation failed',
                    status: 'error',
                    duration: 5000,
                    isClosable: true,
                });
            } else {
                // Continue polling for non-terminal states
                console.log(`⏳ Generation in progress (${data.status}), polling again in ${POLL_INTERVAL}ms`);
                setTimeout(() => pollStatus(blueprintId, 0), POLL_INTERVAL);
            }
        } catch (error) {
            console.error('❌ Polling error:', error);
            
            // Implement retry logic for polling errors
            if (retryCount < MAX_RETRIES) {
                console.log(`🔄 Retrying in ${RETRY_DELAY}ms (attempt ${retryCount + 1}/${MAX_RETRIES})`);
                setTimeout(() => pollStatus(blueprintId, retryCount + 1), RETRY_DELAY);
            } else {
                setIsGenerating(false);
                toast({
                    title: 'Error',
                    description: 'Failed to check blueprint status. Please try refreshing the page.',
                    status: 'error',
                    duration: 5000,
                    isClosable: true,
                });
            }
        }
    };

    return (
        <VStack spacing={8} py={8} px={4}>
            <Card maxW="2xl" w="full">
                <CardBody p={6}>
                    <Heading size="lg" mb={4}>
                        Generate Blueprint using AI
                    </Heading>

                    {isGenerating ? (
                        <VStack spacing={4}>
                            <Progress
                                value={calculateProgress(status)}
                                size="lg"
                                width="full"
                                hasStripe
                                isAnimated
                            />
                            
                            <VStack spacing={2}>
                                <Spinner size="lg" />
                                <Text color="gray.600">
                                    {status?.description || 'Starting generation...'}
                                </Text>
                            </VStack>

                            {status && status.terminal_objectives_count > 0 && (
                                <VStack spacing={1} mt={4} alignItems="flex-start">
                                    <Text fontSize="sm" color="gray.600">
                                        Terminal Objectives: {status.terminal_objectives_count}
                                    </Text>
                                    <Text fontSize="sm" color="gray.600">
                                        Enabling Objectives: {status.enabling_objectives_count}
                                    </Text>
                                </VStack>
                            )}

                            <Button
                                variant="outline"
                                onClick={() => router.push(`/topics/${topicId}`)}
                                width="full"
                            >
                                Continue Browsing
                            </Button>
                        </VStack>
                    ) : (
                        <VStack spacing={4}>
                            <Text color="gray.600">
                                Click generate to start creating an AI-powered assessment blueprint.
                                This process may take a few minutes.
                            </Text>

                            <HStack spacing={2} justifyContent="flex-end" width="full">
                                <Button
                                    variant="outline"
                                    onClick={() => router.push(`/topics/${topicId}`)}
                                >
                                    Cancel
                                </Button>
                                <Button colorScheme="blue" onClick={startGeneration}>
                                    Generate
                                </Button>
                            </HStack>
                        </VStack>
                    )}
                </CardBody>
            </Card>
        </VStack>
    );
}
