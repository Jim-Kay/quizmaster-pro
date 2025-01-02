import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    Box, 
    Button, 
    Typography, 
    Card, 
    CardContent,
    List,
    ListItem,
    ListItemText,
    Divider
} from '@mui/material';
import { BlueprintGeneration } from '../components/BlueprintGeneration';
import { Blueprint } from '../types/blueprint';

export function TopicView() {
    const { topicId } = useParams<{ topicId: string }>();
    const navigate = useNavigate();
    const [generatingBlueprintId, setGeneratingBlueprintId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleGenerateBlueprint = async () => {
        try {
            const response = await fetch(`/api/topics/${topicId}/blueprints/generate`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate blueprint');
            }

            const data: Blueprint = await response.json();
            setGeneratingBlueprintId(data.id);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to generate blueprint');
        }
    };

    // If we're generating a blueprint, show the generation status
    if (generatingBlueprintId) {
        return <BlueprintGeneration blueprintId={generatingBlueprintId} />;
    }

    // Rest of your existing TopicView component...
    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" component="h1" gutterBottom>
                Topic Details
            </Typography>

            {error && (
                <Typography color="error" sx={{ mb: 2 }}>
                    {error}
                </Typography>
            )}

            <Button 
                variant="contained" 
                onClick={handleGenerateBlueprint}
                sx={{ mb: 3 }}
            >
                Generate New Blueprint
            </Button>

            {/* Add your existing topic details and blueprints list here */}
        </Box>
    );
}
