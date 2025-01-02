import { getAuthHeaders } from '../app/auth/auth-utils';

export class UnauthorizedError extends Error {
  constructor(message = 'Unauthorized') {
    super(message);
    this.name = 'UnauthorizedError';
  }
}

export class NotFoundError extends Error {
  constructor(message = 'Not found') {
    super(message);
    this.name = 'NotFoundError';
  }
}

export const assessmentsApi = {
  getAssessmentCount: async (topicId: string, blueprintId: string): Promise<number> => {
    const headers = await getAuthHeaders();
    const response = await fetch(
      `/api/topics/${topicId}/blueprints/${blueprintId}/assessments/count`,
      { headers }
    );
    
    if (!response.ok) {
      if (response.status === 401) {
        throw new UnauthorizedError();
      }
      if (response.status === 404) {
        throw new NotFoundError();
      }
      throw new Error(`API error: ${response.status} - ${await response.text()}`);
    }
    
    const data = await response.json();
    return data.count;
  }
};
