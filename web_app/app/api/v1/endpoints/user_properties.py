#!/usr/bin/env python3
"""
User-Property Association API endpoints
Handles assigning properties to users and retrieving user property assignments
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.property import Property
from app.models.user_property import UserProperty
from app.core.security import get_current_user
from app.schemas.user_property import (
    UserPropertyCreate,
    UserPropertyResponse,
    UserPropertyUpdate,
    UserPropertyList
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/user/{user_id}/properties", response_model=List[UserPropertyResponse])
async def get_user_properties(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all properties assigned to a specific user"""
    # Users can only see their own properties, admins can see any user's properties
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own property assignments"
        )
    
    try:
        # Use joinedload to include user and property data
        user_properties = db.query(UserProperty).options(
            joinedload(UserProperty.user),
            joinedload(UserProperty.property)
        ).filter(UserProperty.user_id == user_id).all()
        
        # Convert SQLAlchemy models to dictionaries for proper serialization
        result = []
        for up in user_properties:
            up_dict = {
                "id": up.id,
                "user_id": up.user_id,
                "property_id": up.property_id,
                "is_primary": up.is_primary,
                "created_at": up.created_at,
                "updated_at": up.updated_at,
                "user": {
                    "id": up.user.id,
                    "username": up.user.username,
                    "email": up.user.email,
                    "first_name": up.user.first_name,
                    "last_name": up.user.last_name,
                    "is_admin": up.user.is_admin
                },
                "property": {
                    "id": up.property.id,
                    "property_code": up.property.property_code,
                    "property_name": up.property.property_name,
                    "is_active": up.property.is_active
                }
            }
            result.append(up_dict)
        
        return result
    except Exception as e:
        logger.error(f"Error getting properties for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user properties"
        )


@router.get("/", response_model=List[UserPropertyResponse])
async def get_all_user_properties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all user-property assignments (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can view all user-property assignments"
        )
    
    try:
        # Use joinedload to include user and property data
        user_properties = db.query(UserProperty).options(
            joinedload(UserProperty.user),
            joinedload(UserProperty.property)
        ).all()
        
        # Convert SQLAlchemy models to dictionaries for proper serialization
        result = []
        for up in user_properties:
            up_dict = {
                "id": up.id,
                "user_id": up.user_id,
                "property_id": up.property_id,
                "is_primary": up.is_primary,
                "created_at": up.created_at,
                "updated_at": up.updated_at,
                "user": {
                    "id": up.user.id,
                    "username": up.user.username,
                    "email": up.user.email,
                    "first_name": up.user.first_name,
                    "last_name": up.user.last_name,
                    "is_admin": up.user.is_admin
                },
                "property": {
                    "id": up.property.id,
                    "property_code": up.property.property_code,
                    "property_name": up.property.property_name,
                    "is_active": up.property.is_active
                }
            }
            result.append(up_dict)
        
        return result
    except Exception as e:
        logger.error(f"Error getting all user-property assignments: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user-property assignments"
        )


@router.get("/my-properties", response_model=List[UserPropertyResponse])
async def get_my_properties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all properties assigned to the current user"""
    try:
        # Use joinedload to include user and property data
        user_properties = db.query(UserProperty).options(
            joinedload(UserProperty.user),
            joinedload(UserProperty.property)
        ).filter(UserProperty.user_id == current_user.id).all()
        
        # Convert SQLAlchemy models to dictionaries for proper serialization
        result = []
        for up in user_properties:
            up_dict = {
                "id": up.id,
                "user_id": up.user_id,
                "property_id": up.property_id,
                "is_primary": up.is_primary,
                "created_at": up.created_at,
                "updated_at": up.updated_at,
                "user": {
                    "id": up.user.id,
                    "username": up.user.username,
                    "email": up.user.email,
                    "first_name": up.user.first_name,
                    "last_name": up.user.last_name,
                    "is_admin": up.user.is_admin
                },
                "property": {
                    "id": up.property.id,
                    "property_code": up.property.property_code,
                    "property_name": up.property.property_name,
                    "is_active": up.property.is_active
                }
            }
            result.append(up_dict)
        
        return result
    except Exception as e:
        logger.error(f"Error getting properties for current user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve your properties"
        )


@router.post("/assign", response_model=UserPropertyResponse)
async def assign_property_to_user(
    assignment: UserPropertyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a property to a user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can assign properties to users"
        )
    
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == assignment.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if property exists
        property_obj = db.query(Property).filter(Property.id == assignment.property_id).first()
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Check if assignment already exists
        existing = db.query(UserProperty).filter(
            UserProperty.user_id == assignment.user_id,
            UserProperty.property_id == assignment.property_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Property is already assigned to this user"
            )
        
        # If this is the first property for the user, make it primary
        if assignment.is_primary:
            # Remove primary flag from other properties for this user
            db.query(UserProperty).filter(
                UserProperty.user_id == assignment.user_id,
                UserProperty.is_primary == True
            ).update({"is_primary": False})
        elif not db.query(UserProperty).filter(UserProperty.user_id == assignment.user_id).first():
            # If no properties exist for user, make this one primary
            assignment.is_primary = True
        
        # Create new assignment
        user_property = UserProperty(**assignment.dict())
        db.add(user_property)
        db.commit()
        db.refresh(user_property)
        
        # Reload with joined data and convert to dictionary for response
        user_property = db.query(UserProperty).options(
            joinedload(UserProperty.user),
            joinedload(UserProperty.property)
        ).filter(UserProperty.id == user_property.id).first()
        
        # Convert to dictionary for proper serialization
        result = {
            "id": user_property.id,
            "user_id": user_property.user_id,
            "property_id": user_property.property_id,
            "is_primary": user_property.is_primary,
            "created_at": user_property.created_at,
            "updated_at": user_property.updated_at,
            "user": {
                "id": user_property.user.id,
                "username": user_property.user.username,
                "email": user_property.user.email,
                "first_name": user_property.user.first_name,
                "last_name": user_property.user.last_name,
                "is_admin": user_property.user.is_admin
            },
            "property": {
                "id": user_property.property.id,
                "property_code": user_property.property.property_code,
                "property_name": user_property.property.property_name,
                "is_active": user_property.property.is_active
            }
        }
        
        logger.info(f"Property {assignment.property_id} assigned to user {assignment.user_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning property to user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to assign property to user"
        )


@router.put("/{assignment_id}", response_model=UserPropertyResponse)
async def update_user_property_assignment(
    assignment_id: int,
    assignment_update: UserPropertyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a user-property assignment (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can update property assignments"
        )
    
    try:
        user_property = db.query(UserProperty).filter(UserProperty.id == assignment_id).first()
        if not user_property:
            raise HTTPException(status_code=404, detail="Property assignment not found")
        
        # Update fields
        for field, value in assignment_update.dict(exclude_unset=True).items():
            if field == "is_primary" and value:
                # Remove primary flag from other properties for this user
                db.query(UserProperty).filter(
                    UserProperty.user_id == user_property.user_id,
                    UserProperty.id != assignment_id,
                    UserProperty.is_primary == True
                ).update({"is_primary": False})
            
            setattr(user_property, field, value)
        
        db.commit()
        db.refresh(user_property)
        
        # Reload with joined data and convert to dictionary for response
        user_property = db.query(UserProperty).options(
            joinedload(UserProperty.user),
            joinedload(UserProperty.property)
        ).filter(UserProperty.id == assignment_id).first()
        
        # Convert to dictionary for proper serialization
        result = {
            "id": user_property.id,
            "user_id": user_property.user_id,
            "property_id": user_property.property_id,
            "is_primary": user_property.is_primary,
            "created_at": user_property.created_at,
            "updated_at": user_property.updated_at,
            "user": {
                "id": user_property.user.id,
                "username": user_property.user.username,
                "email": user_property.user.email,
                "first_name": user_property.user.first_name,
                "last_name": user_property.user.last_name,
                "is_admin": user_property.user.is_admin
            },
            "property": {
                "id": user_property.property.id,
                "property_code": user_property.property.property_code,
                "property_name": user_property.property.property_name,
                "is_active": user_property.property.is_active
            }
        }
        
        logger.info(f"Updated property assignment {assignment_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating property assignment: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update property assignment"
        )


@router.delete("/{assignment_id}")
async def remove_user_property_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a property assignment from a user (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can remove property assignments"
        )
    
    try:
        user_property = db.query(UserProperty).filter(UserProperty.id == assignment_id).first()
        if not user_property:
            raise HTTPException(status_code=404, detail="Property assignment not found")
        
        # If this was the primary property, we might want to set another one as primary
        if user_property.is_primary:
            # Find another property for this user to make primary
            other_property = db.query(UserProperty).filter(
                UserProperty.user_id == user_property.user_id,
                UserProperty.id != assignment_id
            ).first()
            
            if other_property:
                other_property.is_primary = True
        
        db.delete(user_property)
        db.commit()
        
        logger.info(f"Removed property assignment {assignment_id}")
        return {"message": "Property assignment removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing property assignment: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to remove property assignment"
        )


@router.get("/property/{property_id}/users", response_model=List[UserPropertyResponse])
async def get_property_users(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users assigned to a specific property (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can view property user assignments"
        )
    
    try:
        # Use joinedload to include user and property data
        user_properties = db.query(UserProperty).options(
            joinedload(UserProperty.user),
            joinedload(UserProperty.property)
        ).filter(UserProperty.property_id == property_id).all()
        
        # Convert SQLAlchemy models to dictionaries for proper serialization
        result = []
        for up in user_properties:
            up_dict = {
                "id": up.id,
                "user_id": up.user_id,
                "property_id": up.property_id,
                "is_primary": up.is_primary,
                "created_at": up.created_at,
                "updated_at": up.updated_at,
                "user": {
                    "id": up.user.id,
                    "username": up.user.username,
                    "email": up.user.email,
                    "first_name": up.user.first_name,
                    "last_name": up.user.last_name,
                    "is_admin": up.user.is_admin
                },
                "property": {
                    "id": up.property.id,
                    "property_code": up.property.property_code,
                    "property_name": up.property.property_name,
                    "is_active": up.property.is_active
                }
            }
            result.append(up_dict)
        
        return result
    except Exception as e:
        logger.error(f"Error getting users for property {property_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve property users"
        )
