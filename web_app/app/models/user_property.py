#!/usr/bin/env python3
"""
User-Property Association Model
Handles the many-to-many relationship between users and properties
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserProperty(Base):
    """User-Property association table"""
    __tablename__ = "user_properties"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)  # Primary property for the user
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_properties")
    property = relationship("Property", back_populates="user_properties")
    
    class Config:
        orm_mode = True
