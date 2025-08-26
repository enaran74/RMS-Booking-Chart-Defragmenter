"""
Version API endpoint.
Returns current application version based on Git tags and commits.
"""
from fastapi import APIRouter
from datetime import datetime, timedelta
from app.utils.version import get_git_version, get_version_info

router = APIRouter()


@router.get("/version")
async def get_version():
    """
    Get current application version.
    
    Returns version information including Git-based version,
    server timestamp, and additional metadata.
    """
    version_info = get_version_info()
    
    return {
        "version": version_info["version"],
        "timestamp": (datetime.now() + timedelta(hours=10)).isoformat() + "+10:00",  # AEST timestamp
        "is_release": version_info["is_release"],
        "base_version": version_info["base_version"],
        "commits_ahead": version_info["commits_ahead"],
        "commit_hash": version_info["commit_hash"],
        "is_dirty": version_info["is_dirty"],
        "app_name": "RMS Defragmenter"
    }
