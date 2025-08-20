#!/usr/bin/env python3
"""
User-Property Association Pydantic schemas
Handles validation for user-property assignment requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserPropertyBase(BaseModel):
    """Base schema for user-property associations"""
    user_id: int = Field(..., description="ID of the user")
    property_id: int = Field(..., description="ID of the property")
    is_primary: bool = Field(False, description="Whether this is the user's primary property")


class UserPropertyCreate(UserPropertyBase):
    """Schema for creating a new user-property association"""
    pass


class UserPropertyUpdate(BaseModel):
    """Schema for updating a user-property association"""
    is_primary: Optional[bool] = Field(None, description="Whether this is the user's primary property")


class UserPropertyResponse(UserPropertyBase):
    """Schema for user-property association responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Use simple field types that can handle SQLAlchemy model serialization
    user: dict = Field(..., description="User object with username and email")
    property: dict = Field(..., description="Property object with property_name and property_code")
    
    class Config:
        from_attributes = True
        # Allow arbitrary types to handle SQLAlchemy models
        arbitrary_types_allowed = True


class UserPropertyList(BaseModel):
    """Schema for listing user-property associations"""
    assignments: list[UserPropertyResponse]
    total_count: int
    user_id: int
    username: str
