"""
Main API router that includes all endpoint routers
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, defrag_moves, properties

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(defrag_moves.router, prefix="/defrag-moves", tags=["defragmentation moves"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
