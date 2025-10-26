import { auth } from '$lib/stores/auth';

const API_BASE_URL = 'http://localhost:8000/api';

export interface LoginResponse {
  access: string;
  refresh: string;
}

export async function login(username: string, password: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Login failed');
    }

    const data: LoginResponse = await response.json();
    auth.login(username, data.access, data.refresh);
    return true;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

export async function refreshAccessToken(refreshToken: string): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }

    const data: { access: string } = await response.json();
    auth.refreshToken(data.access);
    return data.access;
  } catch (error) {
    console.error('Token refresh failed:', error);
    auth.logout();
    return null;
  }
}

export async function apiFetch<T>(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<T> {
  let { accessToken } = auth;
  
  // If we have a token, add it to the request
  const headers = new Headers(init?.headers);
  const currentAccessToken = auth.accessToken;
  if (currentAccessToken) {
    headers.set('Authorization', `Bearer ${currentAccessToken}`);
  }

  let response = await fetch(input, {
    ...init,
    headers,
  });

  // If token is expired, try to refresh it
  if (response.status === 401 && currentAccessToken) {
    const currentRefreshToken = auth.refreshToken;
    if (currentRefreshToken) {
      const newAccessToken = await refreshAccessToken(currentRefreshToken);
      if (newAccessToken) {
        // Update the auth store with the new token
        auth.updateAccessToken(newAccessToken);
        // Retry the request with the new token
        headers.set('Authorization', `Bearer ${newAccessToken}`);
        response = await fetch(input, {
          ...init,
          headers,
        });
      }
    }
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}
