# Google OAuth API - Postman Testing Guide

## Setup Instructions

### 1. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client ID"
5. Configure the OAuth consent screen if prompted
6. Select "Web application" as the application type
7. Add authorized redirect URIs:
   - `http://localhost:8000/auth/callback`
8. Copy the Client ID and Client Secret

### 2. Configure Environment Variables

Update the `.env` file with your Google OAuth credentials:

```
GOOGLE_CLIENT_ID=your-actual-client-id
GOOGLE_CLIENT_SECRET=your-actual-client-secret
SECRET_KEY=generate-a-random-secret-key-here
```

### 3. Start the Server

```bash
python main.py
```

The server will run on `http://localhost:8000`

## API Endpoints

### 1. Health Check
- **Method**: GET
- **URL**: `http://localhost:8000/health`
- **Description**: Check if the API is running
- **Response**:
  ```json
  {
    "status": "healthy"
  }
  ```

### 2. Root Endpoint
- **Method**: GET
- **URL**: `http://localhost:8000/`
- **Description**: Get API information and available endpoints
- **Response**:
  ```json
  {
    "message": "Google OAuth API",
    "endpoints": {
      "login": "/auth/login",
      "callback": "/auth/callback",
      "me": "/auth/me",
      "logout": "/auth/logout",
      "docs": "/docs"
    }
  }
  ```

### 3. Initiate OAuth Login
- **Method**: GET
- **URL**: `http://localhost:8000/auth/login`
- **Description**: Initiates Google OAuth flow
- **Testing in Postman**:
  1. Make a GET request to this URL
  2. Postman will show you the redirect URL to Google
  3. Copy the redirect URL and open it in a browser
  4. Complete the Google sign-in
  5. You'll be redirected to the callback endpoint with the token

**Alternative (Recommended for Postman)**:
- Use your browser to navigate to `http://localhost:8000/auth/login`
- Complete the OAuth flow
- The callback will return JSON with your access token

### 4. OAuth Callback
- **Method**: GET
- **URL**: `http://localhost:8000/auth/callback`
- **Description**: Handles OAuth callback from Google
- **Note**: This endpoint is called automatically by Google after authentication
- **Response**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "google_id": "1234567890",
      "name": "John Doe",
      "picture": "https://lh3.googleusercontent.com/...",
      "is_active": true,
      "created_at": "2024-01-06T12:00:00",
      "updated_at": "2024-01-06T12:00:00"
    }
  }
  ```

### 5. Get Current User
- **Method**: GET
- **URL**: `http://localhost:8000/auth/me`
- **Headers**:
  ```
  Authorization: Bearer <your-access-token>
  ```
- **Description**: Get current user information
- **Response**:
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "google_id": "1234567890",
    "name": "John Doe",
    "picture": "https://lh3.googleusercontent.com/...",
    "is_active": true,
    "created_at": "2024-01-06T12:00:00",
    "updated_at": "2024-01-06T12:00:00"
  }
  ```

### 6. Logout
- **Method**: POST
- **URL**: `http://localhost:8000/auth/logout`
- **Description**: Logout (client should delete the token)
- **Response**:
  ```json
  {
    "message": "Successfully logged out. Please delete your access token."
  }
  ```

## Testing Flow in Postman

### Step 1: Test Health Check
1. Create a new GET request in Postman
2. URL: `http://localhost:8000/health`
3. Click "Send"
4. Should receive `{"status": "healthy"}`

### Step 2: Complete OAuth Flow (Browser)
1. Open your browser and navigate to: `http://localhost:8000/auth/login`
2. You'll be redirected to Google's login page
3. Sign in with your Google account
4. After successful authentication, you'll be redirected to the callback
5. **Copy the `access_token` from the response**

### Step 3: Test Protected Endpoint
1. Create a new GET request in Postman
2. URL: `http://localhost:8000/auth/me`
3. Go to "Headers" tab
4. Add a new header:
   - Key: `Authorization`
   - Value: `Bearer <paste-your-access-token-here>`
5. Click "Send"
6. You should see your user information

### Step 4: Test Logout
1. Create a new POST request in Postman
2. URL: `http://localhost:8000/auth/logout`
3. Click "Send"
4. Should receive logout confirmation message

## Alternative: Using Postman OAuth 2.0

Postman has built-in OAuth 2.0 support:

1. Create a new request
2. Go to the "Authorization" tab
3. Select "OAuth 2.0" from the Type dropdown
4. Click "Get New Access Token"
5. Configure:
   - Token Name: Google OAuth
   - Grant Type: Authorization Code
   - Callback URL: `http://localhost:8000/auth/callback`
   - Auth URL: `https://accounts.google.com/o/oauth2/v2/auth`
   - Access Token URL: `https://oauth2.googleapis.com/token`
   - Client ID: Your Google Client ID
   - Client Secret: Your Google Client Secret
   - Scope: `openid email profile`
6. Click "Request Token"
7. Complete the Google OAuth flow in the popup
8. Use the token for your requests

## Interactive API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

You can test all endpoints directly from the Swagger UI!

## Common Issues

### Issue: "Missing or invalid authorization header"
- **Solution**: Make sure you're including the Authorization header with "Bearer " prefix

### Issue: "Token has expired"
- **Solution**: Tokens expire after 60 minutes. Get a new token by logging in again

### Issue: "Failed to get user info from Google"
- **Solution**: Check that your Google OAuth credentials are correct in the .env file

### Issue: OAuth redirect not working
- **Solution**: Make sure `http://localhost:8000/auth/callback` is added to your Google OAuth authorized redirect URIs

## Database

The application uses SQLite by default. The database file will be created at `./oauth_app.db` when you start the server for the first time.

## Security Notes

- The `SECRET_KEY` in `.env` is used to sign JWT tokens. Use a strong, random string in production.
- Never commit your `.env` file with real credentials to version control.
- The current setup allows all CORS origins (`allow_origins=["*"]`). In production, restrict this to your frontend domain.
