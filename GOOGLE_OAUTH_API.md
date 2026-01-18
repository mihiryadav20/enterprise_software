# Google OAuth API - React Frontend Integration Guide

## Overview

This document provides instructions for integrating Google OAuth authentication into your React frontend application.

**Base URL:** `http://localhost:8000`

---

## Authentication Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   React     │         │   Backend   │         │   Google    │
│   Frontend  │         │   (FastAPI) │         │   OAuth     │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                       │
       │  1. Click Login       │                       │
       │──────────────────────>│                       │
       │                       │                       │
       │  2. Redirect to Google│                       │
       │<──────────────────────│                       │
       │                       │                       │
       │  3. User authenticates with Google            │
       │───────────────────────────────────────────────>
       │                       │                       │
       │  4. Google redirects to backend callback      │
       │                       │<──────────────────────│
       │                       │                       │
       │  5. Backend redirects to frontend with tokens │
       │<──────────────────────│                       │
       │                       │                       │
       │  6. Frontend stores tokens & fetches user     │
       │──────────────────────>│                       │
       │                       │                       │
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/google/login` | GET | Initiates OAuth flow (redirect) |
| `/auth/google/callback` | GET | OAuth callback (handled by backend) |
| `/auth/google/refresh` | POST | Refresh access token |
| `/auth/google/me` | GET | Get current user info |
| `/auth/google/logout` | POST | Logout (client-side cleanup) |

---

## Step-by-Step Implementation

### 1. Create Auth Context

```jsx
// src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing tokens on mount
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
      fetchUser(accessToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async (token) => {
    try {
      const response = await fetch('http://localhost:8000/auth/google/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else if (response.status === 401) {
        // Token expired, try to refresh
        await refreshToken();
      } else {
        logout();
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const refreshToken = async () => {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) {
      logout();
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/auth/google/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token: refresh })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        setUser(data.user);
      } else {
        logout();
      }
    } catch (error) {
      console.error('Failed to refresh token:', error);
      logout();
    }
  };

  const login = () => {
    // Redirect to backend OAuth endpoint
    window.location.href = 'http://localhost:8000/auth/google/login';
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  const setTokens = (accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      logout,
      refreshToken,
      setTokens,
      fetchUser
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

### 2. Create OAuth Callback Handler

```jsx
// src/pages/AuthCallback.jsx
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const AuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setTokens, fetchUser } = useAuth();
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleCallback = async () => {
      const accessToken = searchParams.get('access_token');
      const refreshToken = searchParams.get('refresh_token');

      if (accessToken && refreshToken) {
        // Store tokens
        setTokens(accessToken, refreshToken);

        // Fetch user data
        await fetchUser(accessToken);

        // Redirect to dashboard or home
        navigate('/dashboard', { replace: true });
      } else {
        setError('Authentication failed. No tokens received.');
      }
    };

    handleCallback();
  }, [searchParams, setTokens, fetchUser, navigate]);

  if (error) {
    return (
      <div className="auth-callback-error">
        <h2>Authentication Failed</h2>
        <p>{error}</p>
        <button onClick={() => navigate('/login')}>
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="auth-callback-loading">
      <p>Completing sign in...</p>
    </div>
  );
};

export default AuthCallback;
```

### 3. Create Error Handler Page

```jsx
// src/pages/AuthError.jsx
import { useSearchParams, useNavigate } from 'react-router-dom';

const AuthError = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const error = searchParams.get('error') || 'An unknown error occurred';

  return (
    <div className="auth-error">
      <h2>Authentication Error</h2>
      <p>{decodeURIComponent(error)}</p>
      <button onClick={() => navigate('/login')}>
        Back to Login
      </button>
    </div>
  );
};

export default AuthError;
```

### 4. Create Login Component

```jsx
// src/components/GoogleLoginButton.jsx
import { useAuth } from '../context/AuthContext';

const GoogleLoginButton = () => {
  const { login } = useAuth();

  return (
    <button
      onClick={login}
      className="google-login-btn"
    >
      <svg viewBox="0 0 24 24" width="20" height="20">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
      Continue with Google
    </button>
  );
};

export default GoogleLoginButton;
```

### 5. Setup Routes

```jsx
// src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import AuthCallback from './pages/AuthCallback';
import AuthError from './pages/AuthError';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/auth/error" element={<AuthError />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
```

### 6. Protected Route Component

```jsx
// src/components/ProtectedRoute.jsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
```

---

## Making Authenticated API Requests

### Using Fetch with Token Refresh

```jsx
// src/utils/api.js
const API_BASE = 'http://localhost:8000';

export const authenticatedFetch = async (endpoint, options = {}) => {
  let accessToken = localStorage.getItem('access_token');

  const makeRequest = async (token) => {
    return fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
  };

  let response = await makeRequest(accessToken);

  // If token expired, try to refresh
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const refreshResponse = await fetch(`${API_BASE}/auth/google/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (refreshResponse.ok) {
      const data = await refreshResponse.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);

      // Retry original request with new token
      response = await makeRequest(data.access_token);
    } else {
      // Refresh failed, clear tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
      throw new Error('Session expired');
    }
  }

  return response;
};
```

### Usage Example

```jsx
// In a component
import { authenticatedFetch } from '../utils/api';

const fetchProtectedData = async () => {
  try {
    const response = await authenticatedFetch('/api/protected-endpoint');
    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error('Request failed:', error);
  }
};
```

---

## API Response Formats

### Successful Authentication (via callback redirect)
The callback redirects to your frontend with URL parameters:
```
http://localhost:5173/auth/callback?access_token=xxx&refresh_token=xxx&token_type=bearer
```

### Refresh Token Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "google_id": "123456789",
    "name": "John Doe",
    "picture": "https://lh3.googleusercontent.com/...",
    "is_active": true,
    "email_verified": true,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
}
```

### Get Current User Response
```json
{
  "id": 1,
  "email": "user@example.com",
  "google_id": "123456789",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "is_active": true,
  "email_verified": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Token has expired"
}
```

**403 Forbidden:**
```json
{
  "detail": "User account is deactivated"
}
```

**404 Not Found:**
```json
{
  "detail": "User not found"
}
```

---

## Token Information

| Token Type | Expiration | Storage |
|------------|------------|---------|
| Access Token | 60 minutes | localStorage |
| Refresh Token | 30 days | localStorage |

**JWT Payload Structure:**
```json
{
  "sub": "1",
  "email": "user@example.com",
  "exp": 1705312200,
  "type": "access"
}
```

---

## Environment Variables

Create a `.env` file in your React project root:

```env
VITE_API_URL=http://localhost:8000
```

Then use it in your code:
```jsx
const API_BASE = import.meta.env.VITE_API_URL;
```

---

## Testing the Flow

1. **Start the backend:**
   ```bash
   cd enterprise_building
   python main.py
   ```

2. **Start your React app:**
   ```bash
   npm run dev
   ```

3. **Test the flow:**
   - Navigate to your login page
   - Click "Continue with Google"
   - Complete Google authentication
   - You should be redirected to `/auth/callback` with tokens
   - The app should extract tokens and redirect to dashboard

---

## Troubleshooting

### Common Issues

**1. CORS Errors**
Ensure the backend allows your frontend origin. The current config allows all origins (`*`).

**2. Callback URL Mismatch**
Make sure the Google Cloud Console has the correct callback URL:
```
http://localhost:8000/auth/google/callback
```

**3. Tokens Not Persisting**
Check browser localStorage:
```javascript
console.log(localStorage.getItem('access_token'));
console.log(localStorage.getItem('refresh_token'));
```

**4. User Not Loading After Refresh**
Ensure `fetchUser` is called on app mount with existing tokens.

---

## Security Considerations

1. **Use HTTPS in production** - Never send tokens over HTTP
2. **Consider httpOnly cookies** - For enhanced security (requires backend changes)
3. **Implement token blacklisting** - For proper logout functionality
4. **Set appropriate CORS origins** - Don't use `*` in production
5. **Validate tokens on every request** - The backend already does this
