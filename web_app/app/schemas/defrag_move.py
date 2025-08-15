"""
Defragmentation move schemas for request/response models
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class DefragMoveBase(BaseModel):
    property_id: int
    move_data: Dict[str, Any]
    suggested_by: Optional[str] = None

class DefragMoveCreate(DefragMoveBase):
    pass

class DefragMoveUpdate(BaseModel):
    status: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

class DefragMoveResponse(DefragMoveBase):
    id: int
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DefragMoveApproval(BaseModel):
    move_id: int
    action: str  # "approve" or "reject"
    notes: Optional[str] = None
