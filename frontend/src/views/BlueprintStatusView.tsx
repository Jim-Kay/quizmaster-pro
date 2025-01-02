import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box,
    Paper,
    Typography,
    CircularProgress,
    Button,
    Alert,
    LinearProgress
} from '@mui/material';
import { BlueprintStatus } from '../types/blueprint';

const POLL_INTERVAL = 5000; // Poll every 5 seconds

export function BlueprintStatusView() {
    const { topicId, blueprintId } = useParams<{ topicId: string; blueprintId: string }>();
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
                    navigate(`/topics/${topicId}/blueprints/${blueprintId}`);
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
    }, [blueprintId, topicId, navigate]);

    if (error) {
        return (
            <Box sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
                <Button 
                    variant="contained" 
                    onClick={() => navigate(`/topics/${topicId}`)}
                >
                    Back to Topic
                </Button>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
            <Paper sx={{ p: 3 }}>
                <Typography variant="h5" gutterBottom>
                    {status?.title || 'Generating Blueprint...'}
                </Typography>

                <LinearProgress sx={{ my: 2 }} />

                <Typography variant="body1" color="text.secondary" gutterBottom>
                    {status?.description || 'Please wait while we generate your blueprint...'}
                </Typography>

                {status?.terminal_objectives_count > 0 && (
                    <Box sx={{ mt: 3 }}>
                        <Typography variant="subtitle2" gutterBottom>
                            Progress:
                        </Typography>
                        <Typography variant="body2">
                            • Terminal Objectives: {status.terminal_objectives_count}
                        </Typography>
                        <Typography variant="body2">
                            • Enabling Objectives: {status.enabling_objectives_count}
                        </Typography>
                    </Box>
                )}

                <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between' }}>
                    <Button 
                        variant="text"
                        onClick={() => navigate(`/topics/${topicId}`)}
                    >
                        Back to Topic
                    </Button>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CircularProgress size={20} />
                        <Typography variant="body2" color="text.secondary">
                            Generation in progress...
                        </Typography>
                    </Box>
                </Box>
            </Paper>
        </Box>
    );
}
