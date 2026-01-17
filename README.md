# fastapi enterprise level practise

### here we will be trying to build our fastapi app as a practise

Day 1: Jan 6 2026

1. working on building an oauth2 that includes Google and a magic link auth.

---

## Magic Link Authentication

This project implements passwordless authentication via email-based magic links.

- **Request a magic link:** Users enter their email and receive a secure, time-limited login link.
- **Verify magic link:** Clicking the link authenticates the user and issues JWT tokens.
- **No password required:** Secure, one-time-use tokens; tokens expire after 15 minutes.

### Quick Start

1. **Set environment variables:**
   - `RESEND_API_KEY`, `FROM_EMAIL`, `FRONTEND_URL`, `SECRET_KEY`
2. **Run the app:**
   ```bash
   uvicorn main:app --reload
   ```
3. **Request a magic link:**
   ```bash
   curl -X POST http://localhost:8000/auth/magic/request \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
   ```
4. **Verify the token:** (get token from email)
   ```bash
   curl -X POST http://localhost:8000/auth/magic/verify \
     -H "Content-Type: application/json" \
     -d '{"token": "YOUR_TOKEN_FROM_EMAIL"}'
   ```
5. **Access user info:**
   ```bash
   curl -X GET http://localhost:8000/auth/magic/me \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### More Info

See [`MAGIC_LINK_API.md`](./MAGIC_LINK_API.md) for full API documentation, error codes, and frontend integration examples.
