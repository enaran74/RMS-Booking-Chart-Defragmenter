#!/usr/bin/env python3
"""
RMS Booking Chart Defragmenter - Web Application
FastAPI-based web interface for managing defragmentation moves
"""

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.core import config as app_config
from app.core.websocket_manager import websocket_manager
from app.middleware.security import (
    SecurityHeadersMiddleware, 
    ErrorSanitizationMiddleware, 
    setup_rate_limiting
)

# Import all models to ensure they are registered with SQLAlchemy BEFORE creating the engine
from app.models.user import User
from app.models.property import Property
from app.models.user_property import UserProperty
from app.models.move_batch import MoveBatch
from app.models.defrag_move import DefragMove

from app.core.database import engine, Base, get_db
from app.api.v1.api import api_router
from app.core.security import create_access_token, get_current_user
from app.schemas.auth import TokenResponse
from app.models.user import User

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

# Add security middleware (order matters - CORS first, then security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.settings.CORS_ORIGINS,
    allow_credentials=app_config.settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=app_config.settings.CORS_ALLOW_METHODS,
    allow_headers=app_config.settings.CORS_ALLOW_HEADERS,
)

# Add security headers middleware
app.add_middleware(
    SecurityHeadersMiddleware,
    enable_csp=True,
    enable_hsts=app_config.settings.DEBUG is False  # Only enable HSTS in production
)

# Add error sanitization middleware
app.add_middleware(
    ErrorSanitizationMiddleware,
    debug_mode=app_config.settings.DEBUG
)

# Setup rate limiting
rate_limiter = setup_rate_limiting(app)

# Security
security = HTTPBearer()

# Templates
templates = Jinja2Templates(directory="app/templates")

# Setup detection middleware (MUST be before static file mounting)
@app.middleware("http")
async def setup_redirect_middleware(request: Request, call_next):
    """Redirect to setup wizard if no admin users exist"""
    
    # Skip middleware for certain paths
    skip_paths = [
        "/api/",
        "/static/",
        "/setup-wizard",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]
    
    # Check if we should skip this request
    if any(request.url.path.startswith(path) for path in skip_paths):
        return await call_next(request)
    
    try:
        # Check if any admin users exist using raw SQL to avoid relationship issues
        from sqlalchemy import text
        db = next(get_db())
        result = db.execute(text("SELECT COUNT(*) FROM users WHERE is_admin = true"))
        admin_count = result.scalar()
        db.close()
        
        # If no admin users exist, redirect to setup wizard
        if admin_count == 0:
            return RedirectResponse(url="/setup-wizard", status_code=302)
            
    except Exception as e:
        # If there's a database error, let the request proceed
        # This prevents the middleware from breaking the app
        logging.warning(f"Setup middleware database check failed: {e}")
    
    return await call_next(request)

# Mount static files (AFTER middleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def read_root(request: Request):
    """Serve the main application page"""
    # Expose training flag to templates for footer badge
    use_training = getattr(app_config.settings, 'USE_TRAINING_DB', True)
    return templates.TemplateResponse("index.html", {"request": request, "active_page": "dashboard", "use_training_db": use_training})

@app.get("/setup")
async def read_setup(request: Request):
    """Serve the admin setup page"""
    use_training = getattr(app_config.settings, 'USE_TRAINING_DB', True)
    return templates.TemplateResponse("setup.html", {"request": request, "active_page": "setup", "use_training_db": use_training})

@app.get("/setup-wizard")
async def read_setup_wizard(request: Request):
    """Serve the first-time setup wizard page"""
    use_training = getattr(app_config.settings, 'USE_TRAINING_DB', True)
    return templates.TemplateResponse("setup_wizard.html", {"request": request, "use_training_db": use_training})

@app.get("/move-history")
async def read_move_history(request: Request):
    """Serve the move history page"""
    use_training = getattr(app_config.settings, 'USE_TRAINING_DB', True)
    return templates.TemplateResponse("move_history.html", {"request": request, "active_page": "move_history", "use_training_db": use_training})

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

@app.websocket("/ws/rms-progress/{property_code}")
async def websocket_rms_progress(websocket: WebSocket, property_code: str):
    """WebSocket endpoint for real-time RMS API progress updates"""
    try:
        # Connect the WebSocket
        await websocket_manager.connect(websocket, property_code.upper())
        
        # Keep the connection alive and handle incoming messages
        while True:
            try:
                # Wait for any message from the client (ping/pong for keep-alive)
                data = await websocket.receive_text()
                
                # Handle ping messages
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                websocket_manager.disconnect(websocket)
                break
                
    except Exception as e:
        logging.error(f"WebSocket error for {property_code}: {e}")
        websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=app_config.settings.WEB_APP_HOST,
        port=app_config.settings.WEB_APP_PORT,
        reload=True
    )
