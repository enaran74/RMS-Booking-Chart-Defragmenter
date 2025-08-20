"""
DefragMove model for storing defragmentation move suggestions
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class DefragMove(Base):
    __tablename__ = "defrag_moves"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    property_code = Column(String(10), nullable=False, index=True)  # Property code for easier querying
    analysis_date = Column(DateTime(timezone=True), nullable=False, index=True)  # When analysis was run
    move_data = Column(JSON, nullable=False)  # Stores the complete move data as JSON
    move_count = Column(Integer, default=0)  # Number of moves in this analysis
    status = Column(String(50), default="pending", index=True)  # pending, approved, rejected, applied
    suggested_by = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # New fields for move management system
    processed_at = Column(DateTime(timezone=True), nullable=True)  # When move was processed
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # User who processed it
    rejected_at = Column(DateTime(timezone=True), nullable=True)  # When move was rejected
    rejected_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # User who rejected it
    batch_id = Column(Integer, ForeignKey("move_batches.id"), nullable=True)  # Batch this move belongs to
    is_processed = Column(Boolean, default=False, nullable=False)  # Quick filter flag
    is_rejected = Column(Boolean, default=False, nullable=False)  # Quick filter flag
    
    # Relationships - use string references to avoid circular imports
    property = relationship("Property", back_populates="defrag_moves")
    processed_by_user = relationship("User", foreign_keys=[processed_by], backref="processed_moves")
    rejected_by_user = relationship("User", foreign_keys=[rejected_by], backref="rejected_moves")
    batch = relationship("MoveBatch", back_populates="moves")
    
    # Indexes for better performance
    __table_args__ = (
        Index('idx_property_analysis_date', 'property_id', 'analysis_date'),
        Index('idx_property_code_analysis_date', 'property_code', 'analysis_date'),
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_batch_id', 'batch_id'),
        Index('idx_status_flags', 'is_processed', 'is_rejected'),
        Index('idx_property_batch', 'property_code', 'batch_id'),
    )
    
    def __repr__(self):
        return f"<DefragMove(id={self.id}, property_code='{self.property_code}', analysis_date='{self.analysis_date}', move_count={self.move_count}, status='{self.status}', is_processed={self.is_processed}, is_rejected={self.is_rejected})>"
