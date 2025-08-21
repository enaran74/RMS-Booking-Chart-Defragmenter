#!/usr/bin/env python3
"""
RMS Booking Chart Defragmenter - Web Application
FastAPI-based web interface for managing defragmentation moves
"""

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
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
from app.core.websocket_manager import websocket_manager

# Import all models to ensure they are registered with SQLAlchemy BEFORE creating the engine
from app.models.user import User
from app.models.property import Property
from app.models.user_property import UserProperty
from app.models.move_batch import MoveBatch
from app.models.defrag_move import DefragMove

from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.core.security import create_access_token, get_current_user
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
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def read_root():
    """Serve the main application page"""
    return FileResponse("app/templates/index.html")

@app.get("/setup")
async def read_setup():
    """Serve the admin setup page"""
    return FileResponse("app/templates/setup.html")

@app.get("/move-history")
async def read_move_history():
    """Serve the move history page"""
    return FileResponse("app/templates/move_history.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RMS Booking Chart Defragmenter Web App",
        "version": "1.0.0"
    }

@app.get("/static/images/dhp_logo_white.svg")
async def serve_logo():
    """Serve the DHP logo directly"""
    logo_path = "app/static/images/dhp_logo_white.svg"
    return FileResponse(logo_path, media_type="image/svg+xml")

@app.get("/static/images/dhp_circle_logo.svg")
async def serve_circle_logo():
    """Serve the DHP circular logo directly for favicon"""
    logo_path = "app/static/images/dhp_circle_logo.svg"
    return FileResponse(logo_path, media_type="image/svg+xml")

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
        host=settings.WEB_APP_HOST,
        port=settings.WEB_APP_PORT,
        reload=True
    )
