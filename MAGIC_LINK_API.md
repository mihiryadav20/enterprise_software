# Magic Link Authentication API

A passwordless authentication system using email-based magic links.

## Overview

Magic link authentication allows users to sign in without a password. When a user requests access, they receive an email containing a unique, time-limited link. Clicking this link authenticates them and provides JWT tokens for subsequent API requests.

## Base URL

```
http://localhost:8000
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `RESEND_API_KEY` | API key from [Resend](https://resend.com) | `re_123abc...` |
| `FROM_EMAIL` | Sender email address (must be verified in Resend) | `auth@yourdomain.com` |
| `FRONTEND_URL` | Frontend URL for magic link redirects | `http://localhost:5173` |
| `SECRET_KEY` | Secret key for JWT signing | `your-secure-secret-key` |

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  1. User enters email    ──────►  POST /auth/magic/request          │
│                                           │                         │
│                                           ▼                         │
│  2. Email sent with magic link    ◄────── Server creates token      │
│                                           │                         │
│                                           ▼                         │
│  3. User clicks link     ──────►  Frontend extracts token           │
│                                           │                         │
│                                           ▼                         │
│  4. Frontend calls       ──────►  POST /auth/magic/verify           │
│                                           │                         │
│                                           ▼                         │
│  5. Receives tokens      ◄────── { access_token, refresh_token }    │
│                                           │                         │
│                                           ▼                         │
│  6. Use access_token     ──────►  GET /auth/magic/me                │
│     for authenticated                     │                         │
│     requests                              ▼                         │
│                                   { user data }                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### 1. Request Magic Link

Sends a magic link to the user's email. Creates a new user account if one doesn't exist.

**Endpoint:** `POST /auth/magic/request`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "message": "Magic link sent! Check your email to sign in."
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 403 | User account is deactivated |
| 422 | Invalid email format |
| 500 | Email service error |

**Example:**
```bash
curl -X POST http://localhost:8000/auth/magic/request \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

---

### 2. Verify Magic Link

Verifies the magic link token and returns JWT access and refresh tokens.

**Endpoint:** `POST /auth/magic/verify`

**Request Body:**
```json
{
  "token": "abc123xyz..."
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "google_id": null,
    "name": null,
    "picture": null,
    "is_active": true,
    "email_verified": true,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  }
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 400 | Invalid or expired magic link |
| 400 | Magic link has already been used |

**Example:**
```bash
curl -X POST http://localhost:8000/auth/magic/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "abc123xyz..."}'
```

---

### 3. Refresh Access Token

Exchanges a refresh token for a new access token and refresh token pair.

**Endpoint:** `POST /auth/magic/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    ...
  }
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Invalid token type (not a refresh token) |
| 401 | Refresh token has expired |
| 401 | Invalid refresh token |
| 403 | User account is deactivated |
| 404 | User not found |

**Example:**
```bash
curl -X POST http://localhost:8000/auth/magic/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

---

### 4. Get Current User

Returns the authenticated user's information.

**Endpoint:** `GET /auth/magic/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "google_id": null,
  "name": null,
  "picture": null,
  "is_active": true,
  "email_verified": true,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Missing or invalid authorization header |
| 401 | Token has expired |
| 401 | Invalid token |
| 401 | Invalid token type (refresh token used instead of access token) |
| 403 | User account is deactivated |
| 404 | User not found |

**Example:**
```bash
curl -X GET http://localhost:8000/auth/magic/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 5. Logout

Informs the client to discard tokens. In a stateless JWT system, actual token invalidation happens client-side.

**Endpoint:** `POST /auth/magic/logout`

**Success Response (200):**
```json
{
  "message": "Successfully logged out. Please discard your tokens on the client side."
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/auth/magic/logout
```

---

## Token Configuration

| Token Type | Expiration | Purpose |
|------------|------------|---------|
| Magic Link Token | 15 minutes | One-time use for email verification |
| Access Token | 60 minutes | API authentication |
| Refresh Token | 30 days | Obtain new access tokens |

## Security Features

- **One-time use tokens:** Magic link tokens are marked as used after verification
- **Token invalidation:** Requesting a new magic link invalidates all previous unused tokens for that user
- **Token type validation:** Access and refresh tokens are typed to prevent misuse
- **Account status checks:** Deactivated accounts cannot authenticate
- **Secure token generation:** Uses `secrets.token_urlsafe(32)` for cryptographically secure tokens

## Frontend Integration Example

```javascript
// 1. Request magic link
async function requestMagicLink(email) {
  const response = await fetch('/auth/magic/request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  return response.json();
}

// 2. Handle magic link callback (e.g., on /auth/verify?token=xxx page)
async function verifyMagicLink(token) {
  const response = await fetch('/auth/magic/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  });
  const data = await response.json();

  // Store tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  return data.user;
}

// 3. Make authenticated requests
async function fetchUser() {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/auth/magic/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}

// 4. Refresh token when access token expires
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await fetch('/auth/magic/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  const data = await response.json();

  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  return data;
}

// 5. Logout
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}
```

## Database Schema

### Users Table

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary Key |
| email | String | Unique, Not Null, Indexed |
| google_id | String | Unique, Nullable |
| name | String | Nullable |
| picture | String | Nullable |
| is_active | Boolean | Default: true |
| email_verified | Boolean | Default: false |
| created_at | DateTime | Auto-set on create |
| updated_at | DateTime | Auto-updated |

### Magic Tokens Table

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary Key |
| token | String | Unique, Not Null, Indexed |
| user_id | Integer | Foreign Key → users.id |
| expires_at | DateTime | Not Null |
| used | Boolean | Default: false |
| created_at | DateTime | Auto-set on create |

## Testing with cURL

```bash
# 1. Request a magic link
curl -X POST http://localhost:8000/auth/magic/request \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 2. Verify the token (get this from the email link)
curl -X POST http://localhost:8000/auth/magic/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_TOKEN_FROM_EMAIL"}'

# 3. Access protected route
curl -X GET http://localhost:8000/auth/magic/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 4. Refresh your tokens
curl -X POST http://localhost:8000/auth/magic/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```
