"""
DefragMove model for storing defragmentation move suggestions
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class DefragMove(Base):
    __tablename__ = "defrag_moves"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    move_data = Column(JSON, nullable=False)  # Stores the complete move data as JSON
    status = Column(String(50), default="pending")  # pending, approved, rejected, applied
    suggested_by = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    property = relationship("Property", back_populates="defrag_moves")
    
    def __repr__(self):
        return f"<DefragMove(id={self.id}, property_id={self.property_id}, status='{self.status}')>"
