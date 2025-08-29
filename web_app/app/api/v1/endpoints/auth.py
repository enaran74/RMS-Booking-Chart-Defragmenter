"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    verify_password, create_access_token, create_refresh_token, verify_token, 
    get_password_hash, get_current_user, validate_password_strength, get_token_expiry_info
)
from app.middleware.security import auth_rate_limit, admin_rate_limit, file_upload_rate_limit
from app.models.user import User
from app.schemas.auth import (
    UserLogin, TokenResponse, UserCreate, UserResponse, UserUpdate, 
    PasswordChange, PasswordReset, UserListResponse, RefreshTokenRequest, TokenStatusResponse
)
from datetime import timedelta, datetime
import logging
import os
import time
import magic
import hashlib
import secrets
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login", response_model=TokenResponse)
@auth_rate_limit()
async def login(
    request: Request,
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """User login endpoint"""
    # Find user by username
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    # Calculate expiry info
    expires_at = datetime.utcnow() + access_token_expires
    expires_in = int(access_token_expires.total_seconds())
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        expires_at=expires_at.isoformat() + "Z"
    )

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """User registration endpoint"""
    logger.info(f"ADMIN CREATE USER: username={user_data.username}, email={user_data.email}, is_admin={user_data.is_admin}")
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, errors = validate_password_strength(user_data.password)
    if not is_valid:
        logger.warning(f"CREATE USER password validation failed: {errors}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet strength requirements",
            headers={"X-Password-Errors": "; ".join(errors)}
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_admin=user_data.is_admin
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"ADMIN CREATE USER: success id={db_user.id}")
    
    return UserResponse.model_validate(db_user)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse.model_validate(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    # Update user fields
    # Only update allowed fields (exclude legacy property_id)
    allowed = {"email", "first_name", "last_name", "is_active", "is_admin", "avatar_url"}
    for field, value in user_update.dict(exclude_unset=True).items():
        if field in allowed:
            setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)

@router.put("/me/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user password"""
    # Verify current password
    if not verify_password(password_change.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    is_valid, errors = validate_password_strength(password_change.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password does not meet strength requirements",
            headers={"X-Password-Errors": "; ".join(errors)}
        )
    
    # Update password
    current_user.password_hash = get_password_hash(password_change.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/refresh", response_model=TokenResponse)
@auth_rate_limit()
async def refresh_access_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    # Verify refresh token
    payload = verify_token(refresh_request.refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists and is active
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token (refresh token stays the same)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Calculate expiry info
    expires_at = datetime.utcnow() + access_token_expires
    expires_in = int(access_token_expires.total_seconds())
    
    # Update last login time to track activity
    user.last_login = datetime.utcnow()
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_request.refresh_token,  # Return same refresh token
        token_type="bearer",
        expires_in=expires_in,
        expires_at=expires_at.isoformat() + "Z"
    )

@router.get("/token-status", response_model=TokenStatusResponse)
async def get_token_status(
    current_user: User = Depends(get_current_user)
):
    """Get current token status and expiry information"""
    # Extract token from current request context
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    
    # This endpoint is called with a valid token (validated by get_current_user)
    # We'll return information about approaching expiry
    return TokenStatusResponse(
        valid=True,
        expires_soon=False,  # Will be handled by frontend
        time_remaining_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/check-token-expiry")
async def check_token_expiry(
    authorization: str = None
):
    """Check token expiry without full authentication"""
    if not authorization or not authorization.startswith("Bearer "):
        return TokenStatusResponse(valid=False)
    
    token = authorization.replace("Bearer ", "")
    expiry_info = get_token_expiry_info(token)
    
    if expiry_info is None:
        return TokenStatusResponse(valid=False)
    
    return TokenStatusResponse(
        valid=not expiry_info["is_expired"],
        expires_at=expiry_info["expires_at"].isoformat() + "Z" if expiry_info["expires_at"] else None,
        expires_in=expiry_info["time_remaining_seconds"],
        expires_soon=expiry_info["expires_soon"],
        time_remaining_seconds=expiry_info["time_remaining_seconds"]
    )

@router.get("/users", response_model=list[UserListResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    users = db.query(User).all()
    return [UserListResponse.model_validate(user) for user in users]

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, errors = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet strength requirements",
            headers={"X-Password-Errors": "; ".join(errors)}
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_admin=user_data.is_admin
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse.model_validate(db_user)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get user to update
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent updating the admin user's admin status
    if user.is_admin and user_update.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove admin privileges from admin users"
        )
    
    # Update user fields
    # Only update allowed fields (exclude legacy property_id)
    allowed = {"email", "first_name", "last_name", "is_active", "is_admin", "avatar_url"}
    for field, value in user_update.dict(exclude_unset=True).items():
        if field in allowed:
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get user to delete
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting admin users
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin users"
        )
    
    # Prevent deleting self
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.put("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_reset: PasswordReset,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset user password (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get user to reset password
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate new password strength
    is_valid, errors = validate_password_strength(password_reset.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password does not meet strength requirements",
            headers={"X-Password-Errors": "; ".join(errors)}
        )
    
    # Update password
    user.password_hash = get_password_hash(password_reset.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.post("/users/{user_id}/avatar")
@file_upload_rate_limit()
async def upload_user_avatar(
    request: Request,
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload or replace a user's avatar (admin or self). Expects a square PNG/JPEG <= 1.5MB.
    The client should pre-crop to 256x256. Server saves to static/uploads/avatars.
    """
    # Permissions: admin or self
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Read file data first for validation
    data = await file.read()
    
    # Enforce max size ~1.5MB
    if len(data) > 1_572_864:
        raise HTTPException(status_code=400, detail="Image too large (max 1.5MB)")
    
    # Validate actual file content using python-magic (more secure than content-type header)
    try:
        file_type = magic.from_buffer(data[:2048], mime=True)
        if file_type not in ["image/png", "image/jpeg"]:
            raise HTTPException(status_code=400, detail="Invalid image format. Only PNG and JPEG are allowed.")
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to validate file type")
    
    # Additional security: Check for malicious patterns
    if b'<script' in data.lower() or b'javascript:' in data.lower():
        raise HTTPException(status_code=400, detail="File contains potentially malicious content")
    
    # Generate secure random filename to prevent path traversal and predictable names
    random_suffix = secrets.token_hex(8)
    file_hash = hashlib.sha256(data).hexdigest()[:8]
    ext = ".png" if file_type == "image/png" else ".jpg"
    filename = f"avatar_{user_id}_{file_hash}_{random_suffix}{ext}"
    
    # Prepare secure path
    base_dir = Path("app/static/uploads/avatars")
    base_dir.mkdir(parents=True, exist_ok=True)
    file_path = base_dir / filename

    # Write file atomically with secure permissions
    tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    try:
        with open(tmp_path, "wb") as f:
            f.write(data)
        # Set secure file permissions (readable by owner and group only)
        tmp_path.chmod(0o644)
        # Atomic rename
        tmp_path.replace(file_path)
    except Exception as e:
        # Clean up temp file if something goes wrong
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Public URL (cache-bust with timestamp)
    ts = int(time.time())
    public_url = f"/static/uploads/avatars/{filename}?ts={ts}"

    # Update user
    user.avatar_url = public_url
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"avatar_url": public_url}

@router.delete("/users/{user_id}/avatar")
async def delete_user_avatar(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a user's avatar (admin or self)."""
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Attempt to remove file on disk if path looks local
    if user.avatar_url:
        try:
            # Strip query param
            path_only = user.avatar_url.split('?')[0]
            # Expecting /static/uploads/avatars/filename
            parts = path_only.strip('/').split('/')
            if len(parts) >= 4 and parts[0] == 'static' and parts[1] == 'uploads' and parts[2] == 'avatars':
                abs_path = os.path.join('app', *parts)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
        except Exception:
            pass

    user.avatar_url = None
    user.updated_at = datetime.utcnow()
    db.commit()
    return {"success": True}
