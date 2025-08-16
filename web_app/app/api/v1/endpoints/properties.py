"""
Properties endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.property import Property
from app.services.rms_service import rms_service
from pydantic import BaseModel

router = APIRouter()

class PropertyResponse(BaseModel):
    id: int
    property_code: str
    property_name: str
    created_at: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[PropertyResponse])
async def get_properties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    force_refresh: bool = Query(False, description="Force refresh from RMS API")
):
    """Get all properties (admin) or user's property, with optional RMS refresh"""
    try:
        # Use RMS service to get properties (will auto-refresh if needed)
        if current_user.is_admin:
            properties = rms_service.get_properties_from_database(db, force_refresh=force_refresh)
        else:
            if current_user.property_id:
                properties = rms_service.get_properties_from_database(db, force_refresh=force_refresh)
                # Filter to only user's property
                properties = [p for p in properties if p.id == current_user.property_id]
            else:
                properties = []
        
        return [PropertyResponse.model_validate(prop) for prop in properties]
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving properties: {str(e)}"
        )

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific property"""
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check if user has access to this property
    if not current_user.is_admin and current_user.property_id != property_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return PropertyResponse.model_validate(property_obj)

@router.post("/refresh", response_model=dict)
async def refresh_properties_from_rms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually refresh properties from RMS API (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, 
            detail="Only administrators can refresh properties"
        )
    
    try:
        success = rms_service.refresh_properties_in_database(db)
        if success:
            return {
                "message": "Properties refreshed successfully from RMS API",
                "timestamp": rms_service.last_property_refresh.isoformat() if rms_service.last_property_refresh else None
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to refresh properties from RMS API"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing properties: {str(e)}"
        )
