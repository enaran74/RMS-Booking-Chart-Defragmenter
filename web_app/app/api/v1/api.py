"""
Main API router that includes all endpoint routers
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, chart, defrag_moves, properties, setup, setup_wizard, user_properties, version

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(chart.router, prefix="/chart", tags=["booking charts"])
api_router.include_router(defrag_moves.router, prefix="/defrag-moves", tags=["defragmentation moves"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(setup.router, prefix="/setup", tags=["setup"])
api_router.include_router(setup_wizard.router, prefix="/setup-wizard", tags=["setup wizard"])
api_router.include_router(user_properties.router, prefix="/user-properties", tags=["user-property associations"])
api_router.include_router(version.router, prefix="", tags=["version"])
