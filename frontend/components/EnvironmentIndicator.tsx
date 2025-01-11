'use client';

import React, { useEffect, useState } from 'react';
import { Box, Tooltip, VStack, Text } from '@chakra-ui/react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/solid';

interface EnvironmentInfo {
  environment: string;
  description: string;
  color: string;
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
        const response = await fetch(`${apiUrl}/api/environment`);
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
  }, []);

  if (error || !envInfo) {
    return (
      <Box
        position="fixed"
        bottom="4"
        right="20"
        bg="red.500"
        color="white"
        px={3}
        py={2}
        borderRadius="md"
        fontSize="sm"
        zIndex={9999}
      >
        Error: {error || 'Loading...'}
      </Box>
    );
  }

  const environmentsMatch = frontendEnv.toLowerCase() === envInfo.environment.toLowerCase();
  const tooltipContent = environmentsMatch 
    ? envInfo.description 
    : `Warning: Environment Mismatch!\nFrontend: ${frontendEnv}\nBackend: ${envInfo.environment}\n\n${envInfo.description}`;

  return (
    <Tooltip label={tooltipContent} placement="top-end">
      <Box
        position="fixed"
        bottom="4"
        right="20"
        px={3}
        py={2}
        borderRadius="md"
        fontSize="sm"
        zIndex={9999}
        display="flex"
        alignItems="center"
        gap={2}
        bg={environmentsMatch ? envInfo.color : 'orange.400'}
        color="white"
      >
        {!environmentsMatch && (
          <ExclamationTriangleIcon width={16} height={16} />
        )}
        <VStack spacing={0} align="flex-end">
          <Text fontSize="xs" opacity={0.8}>Frontend: {frontendEnv}</Text>
          <Text fontSize="xs" opacity={0.8}>Backend: {envInfo.environment}</Text>
        </VStack>
      </Box>
    </Tooltip>
  );
};

export default EnvironmentIndicator;
