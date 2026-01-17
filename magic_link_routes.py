from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User, MagicToken
from schemas import (
    MagicLinkRequest,
    MagicLinkVerify,
    AuthResponse,
    RefreshTokenRequest,
    MessageResponse,
)
from email_service import send_magic_link_email
from jose import jwt, JWTError
from datetime import datetime, timedelta
import secrets
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth/magic", tags=["magic-link-auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30
MAGIC_LINK_EXPIRE_MINUTES = 15


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


def generate_magic_token() -> str:
    """Generate a secure random token for magic links"""
    return secrets.token_urlsafe(32)


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


@router.post("/request", response_model=MessageResponse)
async def request_magic_link(payload: MagicLinkRequest, db: Session = Depends(get_db)):
    """
    Request a magic link to be sent to the user's email.
    If the user doesn't exist, a new account will be created.
    """
    email = payload.email.lower()

    # Find or create user
    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(email=email, is_active=True, email_verified=False)
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is deactivated")

    # Invalidate any existing unused tokens for this user
    db.query(MagicToken).filter(
        MagicToken.user_id == user.id, MagicToken.used == False
    ).update({"used": True})
    db.commit()

    # Create new magic token
    token = generate_magic_token()
    expires_at = datetime.utcnow() + timedelta(minutes=MAGIC_LINK_EXPIRE_MINUTES)

    magic_token = MagicToken(token=token, user_id=user.id, expires_at=expires_at)
    db.add(magic_token)
    db.commit()

    # Send email
    try:
        email_sent = await send_magic_link_email(email, token)
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send magic link email")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email service error: {str(e)}")

    return MessageResponse(
        message="Magic link sent! Check your email to sign in."
    )


@router.post("/verify", response_model=AuthResponse)
async def verify_magic_link(payload: MagicLinkVerify, db: Session = Depends(get_db)):
    """
    Verify a magic link token and return access/refresh tokens.
    """
    magic_token = (
        db.query(MagicToken)
        .filter(MagicToken.token == payload.token)
        .first()
    )

    if not magic_token:
        raise HTTPException(status_code=400, detail="Invalid or expired magic link")

    if magic_token.used:
        raise HTTPException(status_code=400, detail="Magic link has already been used")

    if magic_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Magic link has expired")

    # Mark token as used
    magic_token.used = True

    # Get and update user
    user = magic_token.user
    user.email_verified = True
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Create tokens
    token_data = {"sub": str(user.id), "email": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user.to_dict(),
    )


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
