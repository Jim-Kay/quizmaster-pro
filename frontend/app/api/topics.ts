import { getAuthHeaders } from '../auth/auth-utils';

export interface Topic {
  id: string;
  title: string;
  description: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTopicPayload {
  title: string;
  description: string;
}

export interface UpdateTopicPayload {
  title: string;
  description: string;
}

export class TopicNotFoundError extends Error {
  constructor(message: string = 'Topic not found') {
    super(message);
    this.name = 'TopicNotFoundError';
  }
}

export class UnauthorizedError extends Error {
  constructor(message: string = 'Unauthorized') {
    super(message);
    this.name = 'UnauthorizedError';
  }
}

const API_BASE_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export const topicsApi = {
  async getTopics(): Promise<Topic[]> {
    const headers = await getAuthHeaders();
    console.log('Request headers:', headers);

    const response = await fetch(`${API_BASE_URL}/api/topics`, {
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      const errorText = await response.text();
      console.error('Error response:', errorText);
      throw new Error(`Failed to fetch topics: ${response.status} ${errorText}`);
    }

    return response.json();
  },

  async getTopic(id: string): Promise<Topic> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/topics/${id}`, {
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      if (response.status === 404) {
        throw new TopicNotFoundError();
      }
      const errorText = await response.text();
      throw new Error(`Failed to fetch topic: ${response.status} ${errorText}`);
    }

    return response.json();
  },

  async createTopic(topic: CreateTopicPayload): Promise<Topic> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/topics`, {
      method: 'POST',
      headers,
      credentials: 'include',
      body: JSON.stringify(topic),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      const errorText = await response.text();
      throw new Error(`Failed to create topic: ${response.status} ${errorText}`);
    }

    return response.json();
  },

  async updateTopic(id: string, topic: UpdateTopicPayload): Promise<Topic> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/topics/${id}`, {
      method: 'PATCH',
      headers,
      credentials: 'include',
      body: JSON.stringify(topic),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      if (response.status === 404) {
        throw new TopicNotFoundError();
      }
      const errorText = await response.text();
      throw new Error(`Failed to update topic: ${response.status} ${errorText}`);
    }

    return response.json();
  },

  async deleteTopic(id: string): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/api/topics/${id}`, {
      method: 'DELETE',
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      if (response.status === 404) {
        throw new TopicNotFoundError();
      }
      const errorText = await response.text();
      throw new Error(`Failed to delete topic: ${response.status} ${errorText}`);
    }
  },
};
