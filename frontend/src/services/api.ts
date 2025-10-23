import axios from "axios";
import type { AxiosError, AxiosResponse } from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api/v1/",
  headers: {
    "Content-Type": "application/json",
  },
});

interface LoginResponse {
  access: string;
  refresh: string;
  user?: {
    id: number;
    username: string;
    email: string;
  };
}

export const login = async (username: string, password: string): Promise<LoginResponse> => {
  try {
    const response: AxiosResponse<LoginResponse> = await api.post("/auth/login/", {
      username,
      password,
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const serverError = error as AxiosError<{ error?: string; detail?: string }>;
      if (serverError.response) {
        console.error('Login error response:', serverError.response.data);
        // Handle different error response formats
        const errorMessage = serverError.response.data?.error || 
                           serverError.response.data?.detail || 
                           'Login failed. Please check your credentials.';
        throw new Error(errorMessage);
      }
    }
    console.error('Login error:', error);
    throw new Error('Unable to connect to the server. Please check your connection.');
  }
};


export interface UserProfile {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export const getUserProfile = async (token: string): Promise<UserProfile> => {
  try {
    const response: AxiosResponse<UserProfile> = await api.get("/users/me/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const serverError = error as AxiosError<{ detail?: string }>;
      if (serverError.response) {
        throw new Error(serverError.response.data?.detail || "Failed to fetch user profile");
      }
    }
    throw new Error("Unable to connect to the server.");
  }
};

// Add a response interceptor to handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access (e.g., redirect to login)
      console.error('Unauthorized access - please log in again');
      // You might want to redirect to login page here
      // window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
