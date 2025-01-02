'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import {
  Container,
  Heading,
  VStack,
  FormControl,
  FormLabel,
  Select,
  Input,
  Button,
  useToast,
  Box,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { UserSettings, settingsApi } from '../api/settings';

export default function SettingsPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [openaiKey, setOpenaiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin?callbackUrl=/settings');
      return;
    }

    if (status !== 'authenticated') {
      return;
    }

    fetchSettings();
  }, [status, router]);

  const fetchSettings = async () => {
    try {
      const data = await settingsApi.getSettings();
      setSettings(data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch settings');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const updatedSettings = await settingsApi.updateSettings({
        llm_provider: settings?.llm_provider,
        openai_key: openaiKey || undefined,
        anthropic_key: anthropicKey || undefined,
      });

      setSettings(updatedSettings);
      setOpenaiKey('');
      setAnthropicKey('');
      setSuccess('Settings updated successfully');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update settings');
    } finally {
      setIsLoading(false);
    }
  };

  if (!settings) {
    return (
      <Container maxW="container.md" centerContent py={8}>
        <Box>Loading settings...</Box>
      </Container>
    );
  }

  return (
    <Container maxW="container.md" py={8}>
      <VStack spacing={8} align="stretch">
        <Heading size="lg">Settings</Heading>

        <Box bg="white" shadow="base" borderRadius="lg" p={6}>
          <form onSubmit={handleSubmit}>
            <VStack spacing={6}>
              <FormControl>
                <FormLabel>LLM Provider</FormLabel>
                <Select
                  value={settings.llm_provider}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      llm_provider: e.target.value as 'openai' | 'anthropic',
                    })
                  }
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                </Select>
              </FormControl>

              <FormControl>
                <FormLabel>OpenAI API Key</FormLabel>
                <Input
                  type="password"
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  placeholder={settings.has_openai_key ? '••••••••' : 'Enter OpenAI API key'}
                />
              </FormControl>

              <FormControl>
                <FormLabel>Anthropic API Key</FormLabel>
                <Input
                  type="password"
                  value={anthropicKey}
                  onChange={(e) => setAnthropicKey(e.target.value)}
                  placeholder={settings.has_anthropic_key ? '••••••••' : 'Enter Anthropic API key'}
                />
              </FormControl>

              {error && (
                <Alert status="error">
                  <AlertIcon />
                  {error}
                </Alert>
              )}

              {success && (
                <Alert status="success">
                  <AlertIcon />
                  {success}
                </Alert>
              )}

              <Button
                type="submit"
                colorScheme="blue"
                isLoading={isLoading}
                loadingText="Saving..."
                width="full"
              >
                Save Settings
              </Button>
            </VStack>
          </form>
        </Box>
      </VStack>
    </Container>
  );
}
