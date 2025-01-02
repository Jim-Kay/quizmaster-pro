import { Topic, TopicFormData, topicResponseSchema } from '@/schemas/topic';
import { UnauthorizedError } from '@/errors';

// Error classes
export class TopicNotFoundError extends Error {
  constructor() {
    super('Topic not found');
    this.name = 'TopicNotFoundError';
  }
}

export { UnauthorizedError };

function transformTopicResponse(data: any): Topic {
  console.log('Transforming topic data:', data);
  const transformed = {
    topic_id: data.topic_id,
    title: data.title,
    description: data.description,
    created_at: data.created_at || data.createdAt,
    updated_at: data.updated_at || data.updatedAt,
  };
  
  console.log('Transformed topic:', transformed);
  // Validate the transformed data
  return topicResponseSchema.parse(transformed);
}

// Topics API object
export const topicsApi = {
  getTopics: async (): Promise<Topic[]> => {
    const response = await fetch('/api/topics');
    if (!response.ok) {
      if (response.status === 401) throw new UnauthorizedError();
      throw new Error('Failed to fetch topics');
    }
    const data = await response.json();
    console.log('Raw topics data:', data);
    return data.map(transformTopicResponse);
  },

  getTopic: async (topic_id: string): Promise<Topic> => {
    const response = await fetch(`/api/topics/${topic_id}`);
    if (!response.ok) {
      if (response.status === 401) throw new UnauthorizedError();
      if (response.status === 404) throw new TopicNotFoundError();
      throw new Error('Failed to fetch topic');
    }
    const data = await response.json();
    console.log('Raw topic data:', data);
    const transformed = transformTopicResponse(data);
    console.log('Transformed topic:', transformed);
    return transformed;
  },

  createTopic: async (data: TopicFormData): Promise<Topic> => {
    const response = await fetch('/api/topics', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      if (response.status === 401) throw new UnauthorizedError();
      throw new Error('Failed to create topic');
    }
    const responseData = await response.json();
    return transformTopicResponse(responseData);
  },

  updateTopic: async (topic_id: string, data: TopicFormData): Promise<Topic> => {
    const response = await fetch(`/api/topics/${topic_id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      if (response.status === 401) throw new UnauthorizedError();
      if (response.status === 404) throw new TopicNotFoundError();
      throw new Error('Failed to update topic');
    }
    const responseData = await response.json();
    return transformTopicResponse(responseData);
  },

  deleteTopic: async (topic_id: string): Promise<void> => {
    const response = await fetch(`/api/topics/${topic_id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      if (response.status === 401) throw new UnauthorizedError();
      if (response.status === 404) throw new TopicNotFoundError();
      throw new Error('Failed to delete topic');
    }
  }
};
