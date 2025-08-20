"""
WebSocket manager for real-time RMS API progress updates
"""

import asyncio
import json
from typing import Dict, Set, Optional
from fastapi import WebSocket
from datetime import datetime
import logging

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_properties: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, property_code: str):
        """Connect a new WebSocket for a specific property"""
        await websocket.accept()
        
        if property_code not in self.active_connections:
            self.active_connections[property_code] = set()
        
        self.active_connections[property_code].add(websocket)
        self.connection_properties[websocket] = property_code
        
        logger.info(f"WebSocket connected for property {property_code}. Total connections: {len(self.active_connections[property_code])}")
        
        # Send initial connection confirmation
        await self.send_message(websocket, {
            "type": "connection_established",
            "property_code": property_code,
            "timestamp": datetime.now().isoformat(),
            "message": f"Connected to real-time updates for {property_code}"
        })
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket"""
        property_code = self.connection_properties.get(websocket)
        if property_code and property_code in self.active_connections:
            self.active_connections[property_code].discard(websocket)
            if not self.active_connections[property_code]:
                del self.active_connections[property_code]
        
        if websocket in self.connection_properties:
            del self.connection_properties[websocket]
        
        logger.info(f"WebSocket disconnected from property {property_code}")
    
    async def send_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message, cls=DateTimeEncoder))
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_property(self, property_code: str, message: dict):
        """Broadcast a message to all WebSockets for a specific property"""
        if property_code not in self.active_connections:
            return
        
        disconnected = set()
        # Create a copy of the set to avoid "set changed size during iteration" error
        connections_copy = set(self.active_connections[property_code])
        for websocket in connections_copy:
            try:
                await websocket.send_text(json.dumps(message, cls=DateTimeEncoder))
            except Exception as e:
                logger.error(f"Failed to broadcast to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected WebSockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def send_progress_update(self, property_code: str, step: str, message: str, progress: Optional[float] = None, data: Optional[dict] = None):
        """Send a progress update to all WebSockets for a property"""
        update_message = {
            "type": "progress_update",
            "step": step,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "progress": progress,
            "data": data or {}
        }
        
        await self.broadcast_to_property(property_code, update_message)
        logger.info(f"Progress update for {property_code}: {step} - {message}")
    
    async def send_error(self, property_code: str, error: str, step: str = "unknown"):
        """Send an error message to all WebSockets for a property"""
        error_message = {
            "type": "error",
            "step": step,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_property(property_code, error_message)
        logger.error(f"Error for {property_code} at step {step}: {error}")
    
    async def send_completion(self, property_code: str, result: dict):
        """Send completion message to all WebSockets for a property"""
        completion_message = {
            "type": "completion",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_property(property_code, completion_message)
        logger.info(f"Completion for {property_code}: {result}")
    
    def get_connection_count(self, property_code: str) -> int:
        """Get the number of active connections for a property"""
        return len(self.active_connections.get(property_code, set()))

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
