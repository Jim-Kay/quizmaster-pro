'use client';

import React, { useEffect, useState } from 'react';
import { Box, Tooltip, VStack, Text } from '@chakra-ui/react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/solid';

interface EnvironmentInfo {
  environment: string;
  description: string;
  color: string;
  database_name?: string;
  process_id: number;
}

interface ApiResponse {
  data: EnvironmentInfo;
}

const EnvironmentIndicator: React.FC = () => {
  const [envInfo, setEnvInfo] = useState<EnvironmentInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const frontendEnv = process.env.NODE_ENV || 'development';

  useEffect(() => {
    const fetchEnvironment = async () => {
      try {
        const apiUrl = process.env.BACKEND_URL || 'http://localhost:8000';
        console.log('Fetching environment info from:', `${apiUrl}/api/environment`);
        const response = await fetch(`${apiUrl}/api/environment`, {
          cache: 'no-store',
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        });
        console.log('Response status:', response.status);
        if (!response.ok) {
          throw new Error(`Failed to fetch environment info: ${response.status}`);
        }
        const data = await response.json();
        console.log('Received data:', data);
        const environmentData = data.data || data;
        setEnvInfo(environmentData);
      } catch (error) {
        console.error('Failed to fetch environment info:', error);
        if (error instanceof Error) {
          console.error('Error message:', error.message);
          console.error('Error stack:', error.stack);
        }
        setError(error instanceof Error ? error.message : 'Unknown error');
      }
    };

    fetchEnvironment();
    
    // Refresh environment info every 5 seconds
    const interval = setInterval(fetchEnvironment, 5000);
    return () => clearInterval(interval);
  }, []);

  if (error || !envInfo) {
    return (
      <Box
        position="fixed"
        top="0"
        right="180px"
        m={4}
        p={2}
        bg="red.500"
        color="white"
        borderRadius="md"
        display="flex"
        alignItems="center"
        gap={2}
        zIndex={9999}
      >
        <ExclamationTriangleIcon width={24} height={24} />
        <Text>Error loading environment info</Text>
      </Box>
    );
  }

  return (
    <Box
      position="fixed"
      bottom="0"
      left="0"
      m={4}
      p={2}
      bg={envInfo.color}
      color="white"
      borderRadius="md"
      zIndex={9999}
    >
      <Tooltip
        label={`Frontend: ${frontendEnv}
Backend: ${envInfo.environment}
Database: ${envInfo.database_name || 'Unknown'}
Process ID: ${envInfo.process_id}
${envInfo.description}`}
        placement="top-start"
      >
        <VStack spacing={0} align="flex-end">
          <Text fontWeight="bold">
            {envInfo.environment.toUpperCase()}
          </Text>
          <Text fontSize="xs">
            DB: {envInfo.database_name || 'Unknown'}
          </Text>
        </VStack>
      </Tooltip>
    </Box>
  );
};

export default EnvironmentIndicator;
