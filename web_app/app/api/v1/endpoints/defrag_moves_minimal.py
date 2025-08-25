"""
Minimal defragmentation moves endpoints for debugging
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test-minimal")
async def test_minimal():
    """Ultra minimal test endpoint"""
    return {"success": True, "message": "Minimal router works"}

@router.get("/history")
async def get_move_history():
    """Minimal history endpoint"""
    return {"success": True, "message": "Minimal history endpoint works", "moves": [], "total_count": 0}
