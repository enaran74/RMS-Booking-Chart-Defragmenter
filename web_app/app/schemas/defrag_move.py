"""
Defragmentation move schemas for request/response models
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class DefragMoveBase(BaseModel):
    property_id: int
    property_code: str
    analysis_date: datetime
    move_data: Dict[str, Any]
    move_count: int = 0
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

class DefragMoveSummary(BaseModel):
    """Summary of move suggestions for a property"""
    property_code: str
    property_name: str
    analysis_date: datetime
    move_count: int
    status: str
    last_updated: datetime
    
    class Config:
        from_attributes = True

class DefragMoveDetail(BaseModel):
    """Detailed move suggestion data"""
    id: int
    property_code: str
    analysis_date: datetime
    move_count: int
    status: str
    moves: List[Dict[str, Any]]  # List of individual moves
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
