import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BlueprintStatus } from '../types/blueprint';
import { Alert, Box, CircularProgress, Typography, Button } from '@mui/material';

const POLL_INTERVAL = 5000; // Poll every 5 seconds

interface BlueprintGenerationProps {
    blueprintId: string;
}

export function BlueprintGeneration({ blueprintId }: BlueprintGenerationProps) {
    const [status, setStatus] = useState<BlueprintStatus | null>(null);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        let pollTimer: NodeJS.Timeout;

        const checkStatus = async () => {
            try {
                const response = await fetch(`/api/blueprints/${blueprintId}/status`);
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to fetch status');
                }
                
                const data: BlueprintStatus = await response.json();
                setStatus(data);

                // If generation is complete or errored, stop polling
                if (data.status === 'completed') {
                    navigate(`/blueprints/${blueprintId}`);
                } else if (data.status === 'error') {
                    setError(data.description);
                } else {
                    // Continue polling if still generating
                    pollTimer = setTimeout(checkStatus, POLL_INTERVAL);
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : 'An error occurred');
            }
        };

        // Start polling
        checkStatus();

        // Cleanup
        return () => {
            if (pollTimer) clearTimeout(pollTimer);
        };
    }, [blueprintId, navigate]);

    if (error) {
        return (
            <Box sx={{ p: 3, textAlign: 'center' }}>
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
                <Button 
                    variant="contained" 
                    onClick={() => navigate('/topics')}
                    sx={{ mt: 2 }}
                >
                    Back to Topics
                </Button>
            </Box>
        );
    }

    return (
        <Box sx={{ 
            p: 3, 
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 2
        }}>
            <Typography variant="h4" component="h1">
                {status?.title || 'Generating Blueprint...'}
            </Typography>
            
            <Typography variant="body1" color="text.secondary">
                {status?.description || 'Please wait while we generate your blueprint...'}
            </Typography>

            {status?.terminal_objectives_count > 0 && (
                <Box sx={{ mt: 2 }}>
                    <Typography variant="body2">
                        Terminal Objectives: {status.terminal_objectives_count}
                    </Typography>
                    <Typography variant="body2">
                        Enabling Objectives: {status.enabling_objectives_count}
                    </Typography>
                </Box>
            )}

            <CircularProgress sx={{ mt: 3 }} />

            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                This may take a few minutes...
            </Typography>

            <Button 
                variant="text" 
                onClick={() => navigate('/topics')}
                sx={{ mt: 2 }}
            >
                Continue Browsing
            </Button>
        </Box>
    );
}
