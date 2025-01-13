'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Container,
  Input,
  Text,
  VStack,
  List,
  ListItem,
  Divider,
  Grid,
  GridItem,
  Card,
  CardBody,
  Heading,
  useColorModeValue,
  FormControl,
  FormLabel,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  useToast,
} from '@chakra-ui/react';
import { useSession } from 'next-auth/react';

interface WebSocketMessage {
  type: string;
  message?: string;
  elapsed_seconds?: number;
  remaining_seconds?: number;
  status?: string;
  error?: string;
  total_messages?: number;
  duration_seconds?: number;
}

interface SimulationConfig {
  duration_seconds: number;
  frequency_seconds: number;
  message_prefix: string;
}

// Mock user ID for development
const MOCK_USER_ID = 'f9b5645d-898b-4d58-b10a-a6b50a9d234b';

export default function DevTools() {
  const { data: session } = useSession();
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [config, setConfig] = useState<SimulationConfig>({
    duration_seconds: 30,
    frequency_seconds: 1,
    message_prefix: "Test message"
  });
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const bg = useColorModeValue('white', 'gray.700');
  const toast = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const cleanupWebSocket = () => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = undefined;
    }
    
    if (ws.current) {
      // Remove all event listeners before closing
      ws.current.onopen = null;
      ws.current.onclose = null;
      ws.current.onmessage = null;
      ws.current.onerror = null;
      
      if (ws.current.readyState === WebSocket.OPEN) {
        ws.current.close();
      }
      ws.current = null;
    }
    
    setConnected(false);
    setIsSimulating(false);
  };

  useEffect(() => {
    // Always connect in development mode
    const connect = () => {
      try {
        cleanupWebSocket();

        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/dev/ws/test';
        // Use mock user ID in development
        ws.current = new WebSocket(`${wsUrl}?token=${MOCK_USER_ID}`);

        ws.current.onopen = () => {
          console.log('Connected to WebSocket');
          setConnected(true);
          toast({
            title: "Connected",
            description: "WebSocket connection established",
            status: "success",
            duration: 3000,
            isClosable: true,
          });
        };

        ws.current.onclose = (event) => {
          console.log('Disconnected from WebSocket', event.code, event.reason);
          setConnected(false);
          setIsSimulating(false);

          // Only attempt to reconnect if we haven't cleaned up
          if (ws.current) {
            toast({
              title: "Disconnected",
              description: "Attempting to reconnect...",
              status: "warning",
              duration: 3000,
              isClosable: true,
            });
            // Attempt to reconnect after 5 seconds
            reconnectTimeout.current = setTimeout(connect, 5000);
          }
        };

        ws.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('Received message:', data);
            setMessages(prev => [...prev, data]);
            
            if (data.type === 'simulation_complete') {
              setIsSimulating(false);
            }
          } catch (error) {
            console.error('Error parsing message:', error);
          }
        };

        ws.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          toast({
            title: "Connection Error",
            description: "Failed to connect to WebSocket server",
            status: "error",
            duration: 5000,
            isClosable: true,
          });
        };
      } catch (error) {
        console.error('Error setting up WebSocket:', error);
        toast({
          title: "Connection Error",
          description: "Failed to setup WebSocket connection",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
    };

    connect();

    // Cleanup function
    return () => {
      cleanupWebSocket();
    };
  }, [toast]);

  const startSimulation = () => {
    if (ws.current?.readyState === WebSocket.OPEN && !isSimulating) {
      try {
        setMessages([]);
        ws.current.send(JSON.stringify(config));
        setIsSimulating(true);
      } catch (error) {
        console.error('Error starting simulation:', error);
        toast({
          title: "Simulation Error",
          description: "Failed to start simulation",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
        setIsSimulating(false);
      }
    }
  };

  return (
    <Container maxW="container.lg">
      <Card mt={6} bg={bg}>
        <CardBody>
          <VStack spacing={6} align="stretch">
            <Heading size="lg">DevTools - WebSocket Testing</Heading>
            <Grid templateColumns="repeat(12, 1fr)" gap={6}>
              <GridItem colSpan={{ base: 12, md: 8 }}>
                <VStack spacing={4} align="stretch">
                  <Box 
                    borderWidth="1px" 
                    borderRadius="lg" 
                    height="400px" 
                    overflowY="auto" 
                    p={4}
                  >
                    <List spacing={2}>
                      {messages.map((msg, index) => (
                        <ListItem key={index}>
                          <Text fontWeight={msg.type === 'simulation_complete' ? 'bold' : 'normal'}>
                            {msg.type === 'simulation_started' && 'Simulation started'}
                            {msg.type === 'simulation_update' && msg.message}
                            {msg.type === 'simulation_complete' && `Simulation complete - Sent ${msg.total_messages} messages over ${msg.duration_seconds}s`}
                            {msg.elapsed_seconds !== undefined && msg.type !== 'simulation_complete' && (
                              <Text as="span" color="gray.500" ml={2}>
                                ({msg.elapsed_seconds}s / {msg.remaining_seconds}s remaining)
                              </Text>
                            )}
                          </Text>
                          {index < messages.length - 1 && <Divider my={2} />}
                        </ListItem>
                      ))}
                      <div ref={messagesEndRef} />
                    </List>
                  </Box>
                </VStack>
              </GridItem>
              <GridItem colSpan={{ base: 12, md: 4 }}>
                <VStack spacing={4} align="stretch">
                  <Card>
                    <CardBody>
                      <VStack spacing={4}>
                        <Text fontWeight="bold">Simulation Config</Text>
                        <FormControl>
                          <FormLabel>Duration (seconds)</FormLabel>
                          <NumberInput 
                            value={config.duration_seconds} 
                            min={1} 
                            max={300}
                            onChange={(_, value) => setConfig(prev => ({ ...prev, duration_seconds: value }))}
                          >
                            <NumberInputField />
                            <NumberInputStepper>
                              <NumberIncrementStepper />
                              <NumberDecrementStepper />
                            </NumberInputStepper>
                          </NumberInput>
                        </FormControl>
                        <FormControl>
                          <FormLabel>Frequency (seconds)</FormLabel>
                          <NumberInput 
                            value={config.frequency_seconds} 
                            min={0.1} 
                            max={10}
                            step={0.1}
                            onChange={(_, value) => setConfig(prev => ({ ...prev, frequency_seconds: value }))}
                          >
                            <NumberInputField />
                            <NumberInputStepper>
                              <NumberIncrementStepper />
                              <NumberDecrementStepper />
                            </NumberInputStepper>
                          </NumberInput>
                        </FormControl>
                        <FormControl>
                          <FormLabel>Message Prefix</FormLabel>
                          <Input
                            value={config.message_prefix}
                            onChange={(e) => setConfig(prev => ({ ...prev, message_prefix: e.target.value }))}
                            placeholder="Message prefix..."
                          />
                        </FormControl>
                        <Button
                          colorScheme="blue"
                          onClick={startSimulation}
                          isDisabled={!connected || isSimulating}
                          width="full"
                        >
                          {isSimulating ? 'Simulation Running...' : 'Start Simulation'}
                        </Button>
                      </VStack>
                    </CardBody>
                  </Card>
                  <Card>
                    <CardBody>
                      <Text fontWeight="bold">Status</Text>
                      <Text color={connected ? "green.500" : "red.500"}>
                        {connected ? "Connected" : "Disconnected"}
                      </Text>
                    </CardBody>
                  </Card>
                </VStack>
              </GridItem>
            </Grid>
          </VStack>
        </CardBody>
      </Card>
    </Container>
  );
}
