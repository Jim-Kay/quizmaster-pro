import { getSession } from "next-auth/react";

interface AuthHeaders {
  Authorization?: string;
  [key: string]: string | undefined;
}

export async function getAuthHeaders(): Promise<HeadersInit> {
  try {
    const session = await getSession();
    if (!session?.accessToken) {
      console.warn('No access token found in session:', session);
      return {};
    }

    return {
      'Authorization': `Bearer ${session.accessToken}`,
      'Content-Type': 'application/json',
    };
  } catch (error) {
    console.error('Error getting session:', error);
    return {};
  }
}

// TODO: Implement these functions when adding authentication
// export async function getAuthToken(): Promise<string | null> {
//   // Get token from localStorage, cookie, or state management
//   return localStorage.getItem('auth_token');
// }

// export async function setAuthToken(token: string): Promise<void> {
//   // Store token in localStorage, cookie, or state management
//   localStorage.setItem('auth_token', token);
// }

// export async function removeAuthToken(): Promise<void> {
//   // Remove token from storage
//   localStorage.removeItem('auth_token');
// }
