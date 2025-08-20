from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class MoveBatch(Base):
    __tablename__ = "move_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    property_code = Column(String(10), nullable=False, index=True)  # Property code for this batch
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # When batch was created
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # User who created the batch
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, processing, completed, failed
    total_moves = Column(Integer, default=0, nullable=False)  # Total moves in this batch
    processed_moves = Column(Integer, default=0, nullable=False)  # Number of processed moves
    rejected_moves = Column(Integer, default=0, nullable=False)  # Number of rejected moves
    
    # Relationships - use string references to avoid circular imports
    created_by_user = relationship("User", backref="created_batches")
    moves = relationship("DefragMove", back_populates="batch")
    
    # Indexes for better performance
    __table_args__ = (
        Index('idx_property_status', 'property_code', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_created_by', 'created_by'),
    )
    
    def __repr__(self):
        return f"<MoveBatch(id={self.id}, property_code='{self.property_code}', status='{self.status}', total_moves={self.total_moves}, processed_moves={self.processed_moves}, rejected_moves={self.rejected_moves})>"
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage of the batch"""
        if self.total_moves == 0:
            return 0
        return round(((self.processed_moves + self.rejected_moves) / self.total_moves) * 100, 1)
    
    @property
    def is_complete(self):
        """Check if batch is complete (all moves processed or rejected)"""
        return (self.processed_moves + self.rejected_moves) >= self.total_moves
