"""
Properties endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.property import Property
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
    current_user: User = Depends(get_current_user)
):
    """Get all properties (admin) or user's property"""
    if current_user.is_admin:
        properties = db.query(Property).all()
    else:
        if current_user.property_id:
            properties = db.query(Property).filter(Property.id == current_user.property_id).all()
        else:
            properties = []
    
    return [PropertyResponse.model_validate(prop) for prop in properties]

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
