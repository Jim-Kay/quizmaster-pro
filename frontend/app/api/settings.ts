import { getAuthHeaders } from '../auth/auth-utils';

export interface UserSettings {
  llm_provider: 'openai' | 'anthropic';
  has_openai_key: boolean;
  has_anthropic_key: boolean;
}

export interface UpdateSettingsPayload {
  llm_provider?: 'openai' | 'anthropic';
  openai_key?: string;
  anthropic_key?: string;
}

const API_BASE_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export const settingsApi = {
  async getSettings(): Promise<UserSettings> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/user/settings`, {
      headers,
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized');
      }
      throw new Error(`Failed to fetch settings: ${response.status}`);
    }

    return response.json();
  },

  async updateSettings(settings: UpdateSettingsPayload): Promise<UserSettings> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/user/settings`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify(settings),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized');
      }
      throw new Error(`Failed to update settings: ${response.status}`);
    }

    return response.json();
  },
};
