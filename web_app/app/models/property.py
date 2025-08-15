"""
Property model for managing different properties
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Property(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    property_code = Column(String(50), unique=True, index=True, nullable=False)
    property_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    users = relationship("User", back_populates="property")
    defrag_moves = relationship("DefragMove", back_populates="property")
    
    def __repr__(self):
        return f"<Property(id={self.id}, code='{self.property_code}', name='{self.property_name}')>"
