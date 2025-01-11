'use client';

import React, { useEffect, useState } from 'react';
import { Box, Tooltip } from '@chakra-ui/react';

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
        // Handle both direct response and wrapped response
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
    // Return an error indicator instead of null
    return (
      <Box
        position="fixed"
        bottom="4"
        right="4"
        px="4"
        py="2"
        borderRadius="md"
        bg="red.500"
        color="white"
        fontWeight="bold"
        boxShadow="md"
        zIndex={1000}
      >
        ENV ERROR
      </Box>
    );
  }

  return (
    <Tooltip label={envInfo.description} placement="left">
      <Box
        position="fixed"
        bottom="4"
        right="4"
        px="4"
        py="2"
        borderRadius="md"
        bg={envInfo.color}
        color="white"
        fontWeight="bold"
        boxShadow="md"
        zIndex={1000}
        display="flex"
        alignItems="center"
        gap="2"
        cursor="help"
      >
        <Box
          w="3"
          h="3"
          borderRadius="full"
          bg="white"
          opacity={0.8}
        />
        {envInfo.environment.toUpperCase()}
      </Box>
    </Tooltip>
  );
};

export default EnvironmentIndicator;
