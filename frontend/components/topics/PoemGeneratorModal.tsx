import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  Progress,
  Box,
  Text,
  Alert,
  AlertIcon,
  AlertDescription,
  Code,
  VStack
} from '@chakra-ui/react';

interface PoemGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  logs: string;
  error: string | null;
  status: string | null;
  onRetry: () => void;
  logsEndRef: React.RefObject<HTMLDivElement>;
}

export function PoemGeneratorModal({
  isOpen,
  onClose,
  logs,
  error,
  status,
  onRetry,
  logsEndRef
}: PoemGeneratorModalProps) {
  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      size="2xl"
      scrollBehavior="inside"
      isCentered
    >
      <ModalOverlay />
      <ModalContent maxH="80vh">
        <ModalHeader>Writing a Poem</ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          {error ? (
            <Alert status="error" variant="left-accent">
              <AlertIcon />
              <VStack align="start" spacing={2} flex={1}>
                <AlertDescription>
                  {error === 'Authentication failed. Please sign in again.' ? (
                    <>
                      Your session has expired. Please{' '}
                      <Button
                        variant="link"
                        colorScheme="red"
                        onClick={() => window.location.href = '/auth/signin'}
                        size="sm"
                      >
                        sign in
                      </Button>
                      {' '}again.
                    </>
                  ) : error}
                </AlertDescription>
                {error !== 'Authentication failed. Please sign in again.' && (
                  <Button
                    variant="link"
                    colorScheme="red"
                    onClick={onRetry}
                    size="sm"
                  >
                    Retry Generation
                  </Button>
                )}
              </VStack>
            </Alert>
          ) : (
            <VStack spacing={4} align="stretch">
              <Box>
                <Progress
                  value={status === 'completed' ? 100 : status === 'failed' ? 100 : 75}
                  colorScheme={
                    status === 'completed'
                      ? 'green'
                      : status === 'failed'
                      ? 'red'
                      : 'blue'
                  }
                  isIndeterminate={status === 'running'}
                  borderRadius="full"
                />
                <Text mt={2} fontSize="sm" color="gray.500">
                  {status || 'pending'}
                </Text>
              </Box>

              <Box
                bg="black"
                color="green.400"
                p={4}
                borderRadius="md"
                height="96"
                overflow="auto"
                fontFamily="mono"
              >
                <Code variant="unstyled" display="block" whiteSpace="pre-wrap">
                  {logs || 'Initializing...'}
                </Code>
                <Box ref={logsEndRef} />
              </Box>
            </VStack>
          )}
        </ModalBody>

        <ModalFooter>
          <Button onClick={onClose}>Close</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
