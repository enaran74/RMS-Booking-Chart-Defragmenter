#!/usr/bin/env python3
"""
RMS Booking Chart Defragmenter - Web Application
FastAPI-based web interface for managing defragmentation moves
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
import uvicorn
import os
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.core.security import create_access_token, get_current_user
from app.models.user import User
from app.schemas.auth import TokenResponse

# Create database tables
Base.metadata.create_all(bind=engine)

# FastAPI app instance
app = FastAPI(
    title="RMS Booking Chart Defragmenter",
    description="Web interface for managing RMS booking chart defragmentation moves",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security
security = HTTPBearer()

# Templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - serves the main application page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RMS Booking Chart Defragmenter Web App",
        "version": "1.0.0"
    }

@app.post("/auth/login", response_model=TokenResponse)
async def login(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Login endpoint for authentication"""
    # This is a placeholder - implement actual authentication logic
    # For now, return a dummy token
    token = create_access_token(data={"sub": "test_user"})
    return TokenResponse(access_token=token, token_type="bearer")

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    """Protected route example"""
    return {"message": f"Hello {current_user.username}, this is a protected route!"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.WEB_APP_HOST,
        port=settings.WEB_APP_PORT,
        reload=True
    )
