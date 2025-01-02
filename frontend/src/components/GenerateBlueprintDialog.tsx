import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalBody,
    ModalFooter,
    ModalCloseButton,
    Button,
    Box,
    Text,
    Spinner,
    VStack,
    Flex,
    useColorModeValue
} from '@chakra-ui/react';
import { Blueprint } from '../types/blueprint';

interface GenerateBlueprintDialogProps {
    isOpen: boolean;
    onClose: () => void;
    topicId: string;
    topicTitle: string;
    topicDescription: string;
}

export function GenerateBlueprintDialog({
    isOpen,
    onClose,
    topicId,
    topicTitle,
    topicDescription
}: GenerateBlueprintDialogProps) {
    const router = useRouter();
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const bgColor = useColorModeValue('gray.50', 'gray.700');

    const handleGenerate = async () => {
        setIsGenerating(true);
        setError(null);

        try {
            const response = await fetch(`/api/topics/${topicId}/blueprints/generate`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate blueprint');
            }

            const data: Blueprint = await response.json();
            onClose();
            router.push(`/topics/${topicId}/blueprints/${data.id}/status`);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to generate blueprint');
            setIsGenerating(false);
        }
    };

    return (
        <Modal 
            isOpen={isOpen} 
            onClose={!isGenerating ? onClose : () => {}}
            size="md"
            isCentered
        >
            <ModalOverlay />
            <ModalContent>
                <ModalHeader>
                    Generate Blueprint using AI
                    {!isGenerating && <ModalCloseButton />}
                </ModalHeader>

                <ModalBody>
                    <Text mb={4}>
                        Generate an assessment blueprint for the following topic using AI:
                    </Text>

                    <Box 
                        bg={bgColor}
                        p={4} 
                        borderRadius="md"
                        mb={4}
                    >
                        <Text fontSize="lg" fontWeight="bold">
                            {topicTitle}
                        </Text>
                        <Text fontSize="sm" color="gray.500">
                            {topicDescription}
                        </Text>
                    </Box>

                    {error && (
                        <Text color="red.500" mt={2}>
                            {error}
                        </Text>
                    )}

                    {isGenerating && (
                        <VStack spacing={4} mt={4}>
                            <Spinner />
                            <Text fontSize="sm" color="gray.500">
                                Starting generation...
                            </Text>
                        </VStack>
                    )}
                </ModalBody>

                <ModalFooter>
                    <Button 
                        onClick={onClose} 
                        isDisabled={isGenerating}
                        mr={3}
                    >
                        Cancel
                    </Button>
                    <Button 
                        onClick={handleGenerate}
                        colorScheme="blue"
                        isDisabled={isGenerating}
                        leftIcon={isGenerating ? <Spinner size="sm" /> : undefined}
                    >
                        Generate
                    </Button>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
}
