"""
Version API endpoint.
Returns current application version based on Git tags and commits.
"""
from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime
import os
import pytz
from app.utils.version import get_git_version, get_version_info

router = APIRouter()


@router.get("/version")
async def get_version():
    """
    Get current application version.
    
    Returns version information including Git-based version,
    server timestamp, and additional metadata.
    """
    logging.info("[version] /version called")
    version_info = get_version_info()
    logging.info(f"[version] resolved version_info: {version_info}")
    
    # Get timezone from environment variable, default to Australia/Sydney
    tz_name = os.getenv('TZ', 'Australia/Sydney')
    try:
        timezone = pytz.timezone(tz_name)
        # Prefer VERSION_INFO modified time if available for a stable build timestamp
        build_ts = None
        for p in ["/app/web/VERSION_INFO", "/app/app/VERSION_INFO"]:
            if os.path.exists(p):
                try:
                    build_ts = datetime.fromtimestamp(os.path.getmtime(p), tz=timezone)
                    break
                except Exception:
                    pass
        if build_ts is None:
            build_ts = datetime.now(timezone)
        timestamp = build_ts.isoformat()
    except Exception:
        # Fallback to UTC if timezone parsing fails
        timestamp = datetime.utcnow().isoformat() + "Z"
    
    result = {
        "version": version_info["version"],
        "timestamp": timestamp,
        "is_release": version_info["is_release"],
        "base_version": version_info["base_version"],
        "commits_ahead": version_info["commits_ahead"],
        "commit_hash": version_info["commit_hash"],
        "is_dirty": version_info["is_dirty"],
        "app_name": "RMS Defragmenter"
    }
    logging.info(f"[version] response: {result}")
    return result


@router.get("/version/static")
async def get_static_version():
    """Return version by reading mounted VERSION_INFO directly, no git call."""
    try:
        logging.info("[version] /version/static called")
        # Preferred container path; fallback paths kept for resilience
        candidates = [
            "/app/web/VERSION_INFO",
            "/app/app/VERSION_INFO",
        ]
        for path in candidates:
            if os.path.exists(path):
                logging.info(f"[version] reading version file: {path}")
                with open(path, "r") as f:
                    version = f.read().strip()
                # Use TZ env for timestamp
                tz_name = os.getenv('TZ', 'Australia/Sydney')
                try:
                    timezone = pytz.timezone(tz_name)
                    # Use file modified time for stable build timestamp
                    timestamp = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone).isoformat()
                except Exception:
                    timestamp = datetime.utcnow().isoformat() + "Z"
                result = {"version": version, "timestamp": timestamp}
                logging.info(f"[version] static response: {result}")
                return result
        raise FileNotFoundError("VERSION_INFO not found")
    except Exception as e:
        logging.error(f"[version] static error: {e}")
        raise HTTPException(status_code=500, detail=f"Static version error: {e}")
