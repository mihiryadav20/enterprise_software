const API_BASE_URL = '/api';

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login/`,
    REFRESH: `${API_BASE_URL}/auth/refresh/`,
    VERIFY: `${API_BASE_URL}/auth/verify/`,
    BLACKLIST: `${API_BASE_URL}/auth/blacklist/`,
    ME: `${API_BASE_URL}/users/me/`,
  },
  // Add more API endpoints here as needed
  // Example:
  // USERS: {
  //   LIST: `${API_BASE_URL}/users/`,
  //   DETAIL: (id: string | number) => `${API_BASE_URL}/users/${id}/`,
  // },
} as const;

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

interface ApiRequestOptions extends Omit<RequestInit, 'body'> {
  method?: HttpMethod;
  headers?: HeadersInit;
  body?: BodyInit | object | null;
  includeAuth?: boolean;
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  // Stringify body if it's an object and not already a string/Blob/FormData
  const body = options.body && typeof options.body === 'object' && 
    !(options.body instanceof Blob) && 
    !(options.body instanceof FormData) &&
    !(options.body instanceof URLSearchParams) &&
    !(options.body instanceof ReadableStream)
      ? JSON.stringify(options.body)
      : options.body as BodyInit | null | undefined;
  const {
    method = 'GET',
    headers = {},
    body: requestBody,
    includeAuth = true,
    ...restOptions
  } = options;

  // Set up headers
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Add auth token if needed
  if (includeAuth) {
    const token = localStorage.getItem('authToken');
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  // Prepare request config
  const config: RequestInit = {
    method,
    headers: {
      ...defaultHeaders,
      ...headers,
    },
    ...restOptions,
  };

  // Handle request body
  if (body) {
    config.body = typeof body === 'object' ? JSON.stringify(body) : body;
  }

  try {
    const response = await fetch(endpoint, {
      ...config,
      body, // Use the processed body
    });
    
    // Handle non-OK responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || 
        errorData.message || 
        `API request failed with status ${response.status}`
      );
    }

    // Handle empty responses (like 204 No Content)
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

// Auth API functions
export const authApi = {
  login: async (credentials: { username: string; password: string }) => {
    return apiRequest(API_ENDPOINTS.AUTH.LOGIN, {
      method: 'POST',
      body: credentials,
      includeAuth: false,
    });
  },

  logout: async () => {
    // Get the refresh token from localStorage or wherever you store it
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (refreshToken) {
      try {
        // Blacklist the refresh token
        await apiRequest(API_ENDPOINTS.AUTH.BLACKLIST, {
          method: 'POST',
          body: { refresh: refreshToken },
          includeAuth: true,
        });
      } catch (error) {
        console.error('Error during logout:', error);
        // Even if blacklist fails, we should still clear the tokens
      }
      
      // Clear tokens from storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
    
    return Promise.resolve();
  },

  getCurrentUser: async () => {
    return apiRequest(API_ENDPOINTS.AUTH.ME);
  },

  refreshToken: async (refreshToken: string) => {
    return apiRequest(API_ENDPOINTS.AUTH.REFRESH, {
      method: 'POST',
      body: { refresh: refreshToken },
      includeAuth: false,
    });
  },
};

// Example usage:
// import { authApi } from '$lib/api';
// 
// try {
//   const user = await authApi.login({ username: 'user', password: 'pass' });
//   console.log('Login successful', user);
// } catch (error) {
//   console.error('Login failed', error);
// }
