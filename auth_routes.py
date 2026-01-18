from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from oauth_config import oauth
from database import get_db
from models import User
from schemas import AuthResponse, RefreshTokenRequest, MessageResponse
from jose import jwt, JWTError
from datetime import datetime, timedelta
from urllib.parse import urlencode
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth/google", tags=["google-oauth"])

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency to get the current authenticated user from JWT token"""
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = int(payload.get("sub"))

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is deactivated")

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/login")
async def login(request: Request):
    """
    Initiate Google OAuth login flow.
    This redirects the user to Google's OAuth consent screen.
    """
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback", name="google_callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle the OAuth callback from Google.
    Exchanges authorization code for tokens and redirects to frontend with JWT tokens.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')

        if not user_info:
            error_params = urlencode({"error": "Failed to get user info from Google"})
            return RedirectResponse(url=f"{FRONTEND_URL}/auth/error?{error_params}")

        # Check if user exists by google_id first, then by email
        user = db.query(User).filter(User.google_id == user_info['sub']).first()

        if not user:
            # Check if user exists with same email (e.g., from magic link)
            user = db.query(User).filter(User.email == user_info.get('email')).first()

            if user:
                # Link Google account to existing user
                user.google_id = user_info.get('sub')
                user.name = user_info.get('name') or user.name
                user.picture = user_info.get('picture') or user.picture
                user.email_verified = True
                user.updated_at = datetime.utcnow()
            else:
                # Create new user
                user = User(
                    email=user_info.get('email'),
                    google_id=user_info.get('sub'),
                    name=user_info.get('name'),
                    picture=user_info.get('picture'),
                    is_active=True,
                    email_verified=True  # Google verified the email
                )
                db.add(user)
        else:
            # Update existing user info
            user.name = user_info.get('name') or user.name
            user.picture = user_info.get('picture') or user.picture
            user.email_verified = True
            user.updated_at = datetime.utcnow()

        # Check if user is active
        if not user.is_active:
            error_params = urlencode({"error": "User account is deactivated"})
            return RedirectResponse(url=f"{FRONTEND_URL}/auth/error?{error_params}")

        db.commit()
        db.refresh(user)

        # Create tokens
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Redirect to frontend with tokens
        params = urlencode({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        })
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?{params}")

    except Exception as e:
        error_params = urlencode({"error": f"Authentication failed: {str(e)}"})
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/error?{error_params}")


@router.post("/refresh", response_model=AuthResponse)
async def refresh_access_token(
    payload: RefreshTokenRequest, db: Session = Depends(get_db)
):
    """
    Get a new access token using a refresh token.
    """
    try:
        token_payload = jwt.decode(
            payload.refresh_token, SECRET_KEY, algorithms=[ALGORITHM]
        )

        if token_payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = int(token_payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is deactivated")

        # Create new tokens
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user.to_dict(),
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's information.
    Requires Bearer token in Authorization header.
    """
    return current_user.to_dict()


@router.post("/logout", response_model=MessageResponse)
async def logout():
    """
    Logout endpoint.
    In a stateless JWT system, the client should discard the tokens.
    For enhanced security, consider implementing a token blacklist.
    """
    return MessageResponse(
        message="Successfully logged out. Please discard your tokens on the client side."
    )
