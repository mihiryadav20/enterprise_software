from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from oauth_config import oauth
from database import get_db
from models import User
from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth", tags=["authentication"])

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.get("/login")
async def login(request: Request):
    """
    Initiate Google OAuth login flow.
    This redirects the user to Google's OAuth consent screen.
    """
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle the OAuth callback from Google.
    This endpoint receives the authorization code and exchanges it for user information.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")

        # Check if user exists
        user = db.query(User).filter(User.google_id == user_info['sub']).first()

        if not user:
            # Create new user
            user = User(
                email=user_info.get('email'),
                google_id=user_info.get('sub'),
                name=user_info.get('name'),
                picture=user_info.get('picture')
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user info
            user.name = user_info.get('name')
            user.picture = user_info.get('picture')
            user.updated_at = datetime.utcnow()
            db.commit()

        # Create access token
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

        # Return token and user info
        return JSONResponse({
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_dict()
        })

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@router.get("/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Get current user information using the access token.
    Pass the token in the Authorization header as: Bearer <token>
    """
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return user.to_dict()

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/logout")
async def logout():
    """
    Logout endpoint. In a token-based system, the client should delete the token.
    """
    return {"message": "Successfully logged out. Please delete your access token."}
