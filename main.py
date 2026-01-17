from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from auth_routes import router as auth_router
from magic_link_routes import router as magic_link_router
from database import init_db
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Authentication API",
    description="API with Google OAuth and Magic Link authentication",
    version="1.0.0"
)

# Add session middleware (required for OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-change-this")
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(magic_link_router)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Authentication API",
        "endpoints": {
            "google_oauth": {
                "login": "/auth/login",
                "callback": "/auth/callback",
                "me": "/auth/me",
                "logout": "/auth/logout"
            },
            "magic_link": {
                "request": "/auth/magic/request",
                "verify": "/auth/magic/verify",
                "refresh": "/auth/magic/refresh",
                "me": "/auth/magic/me",
                "logout": "/auth/magic/logout"
            },
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
