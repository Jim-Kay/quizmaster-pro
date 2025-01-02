import { Blueprint } from '../schemas/blueprint';
import { getAuthHeaders } from '../app/auth/auth-utils';

// Error classes
export class UnauthorizedError extends Error {
  constructor(message = 'Unauthorized') {
    super(message);
    this.name = 'UnauthorizedError';
  }
}

export class BlueprintNotFoundError extends Error {
  constructor(message = 'Blueprint not found') {
    super(message);
    this.name = 'BlueprintNotFoundError';
  }
}

export class TopicNotFoundError extends Error {
  constructor() {
    super('Topic not found or you do not have permission to access it');
    this.name = 'TopicNotFoundError';
  }
}

// Blueprints API object
export const blueprintsApi = {
  getBlueprintCount: async (topicId: string): Promise<number> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`/api/topics/${topicId}/blueprints/count`, {
      headers,
    });
    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      if (response.status === 404) {
        throw new TopicNotFoundError();
      }
      throw new Error(`API error: ${response.status} - ${await response.text()}`);
    }
    const data = await response.json();
    return data.count;
  },

  getBlueprints: async (topicId: string): Promise<Blueprint[]> => {
    console.log('Fetching blueprints for topic:', topicId);
    const response = await fetch(`/api/topics/${topicId}/blueprints`, {
      headers: await getAuthHeaders(),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      if (response.status === 404) {
        console.error('Topic not found or no permission:', await response.text());
        throw new TopicNotFoundError();
      }
      const errorText = await response.text();
      console.error('Failed to fetch blueprints:', errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    console.log('Received blueprints:', data);
    return data;
  },

  generateBlueprint: async (topicId: string): Promise<Blueprint> => {
    const response = await fetch(`/api/topics/${topicId}/blueprints/generate`, {
      method: 'POST',
      headers: await getAuthHeaders(),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      if (response.status === 404) {
        throw new TopicNotFoundError();
      }
      const errorText = await response.text();
      console.error('Failed to generate blueprint:', errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    console.log('Generated blueprint:', data);
    return data;
  },

  deleteBlueprint: async (topicId: string, blueprintId: string): Promise<void> => {
    const response = await fetch(`/api/topics/${topicId}/blueprints/${blueprintId}`, {
      method: 'DELETE',
      headers: await getAuthHeaders(),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      if (response.status === 404) {
        const errorText = await response.text();
        console.error('Blueprint or topic not found:', errorText);
        if (errorText.includes('Topic not found')) {
          throw new TopicNotFoundError();
        }
        throw new BlueprintNotFoundError();
      }
      const errorText = await response.text();
      console.error('Failed to delete blueprint:', errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }
  },

  getBlueprint: async (topicId: string, blueprintId: string): Promise<Blueprint> => {
    const response = await fetch(`/api/topics/${topicId}/blueprints/${blueprintId}`, {
      headers: await getAuthHeaders(),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      if (response.status === 404) {
        const errorText = await response.text();
        console.error('Blueprint or topic not found:', errorText);
        if (errorText.includes('Topic not found')) {
          throw new TopicNotFoundError();
        }
        throw new BlueprintNotFoundError();
      }
      const errorText = await response.text();
      console.error('Failed to get blueprint:', errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    return await response.json();
  },

  updateBlueprint: async (topicId: string, blueprintId: string, blueprint: Partial<Blueprint>): Promise<Blueprint> => {
    const response = await fetch(`/api/topics/${topicId}/blueprints/${blueprintId}`, {
      method: 'PUT',
      headers: {
        ...(await getAuthHeaders()),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(blueprint),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      if (response.status === 404) {
        const errorText = await response.text();
        console.error('Blueprint or topic not found:', errorText);
        if (errorText.includes('Topic not found')) {
          throw new TopicNotFoundError();
        }
        throw new BlueprintNotFoundError();
      }
      const errorText = await response.text();
      console.error('Failed to update blueprint:', errorText);
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    return await response.json();
  }
};
