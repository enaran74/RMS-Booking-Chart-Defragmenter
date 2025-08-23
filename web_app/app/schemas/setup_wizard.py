"""
Pydantic schemas for the setup wizard
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional


class SetupWizardData(BaseModel):
    """Schema for setup wizard completion data"""
    
    # Admin account
    adminUsername: str
    adminPassword: str
    adminEmail: Optional[EmailStr] = None
    
    # RMS API credentials
    agentId: str
    agentPassword: str
    clientId: str
    clientPassword: str
    
    # System configuration
    systemMode: str  # 'training' or 'live'
    propertyMode: str  # 'ALL' or 'SPECIFIC'
    targetProperties: str  # 'ALL' or comma-separated property codes
    timezone: Optional[str] = "Australia/Sydney"
    
    @validator('adminUsername')
    def validate_username(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v.strip()
    
    @validator('adminPassword')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('systemMode')
    def validate_system_mode(cls, v):
        if v not in ['training', 'live']:
            raise ValueError('System mode must be either "training" or "live"')
        return v
    
    @validator('propertyMode')
    def validate_property_mode(cls, v):
        if v not in ['ALL', 'SPECIFIC']:
            raise ValueError('Property mode must be either "ALL" or "SPECIFIC"')
        return v
    
    @validator('agentId', 'agentPassword', 'clientId', 'clientPassword')
    def validate_rms_credentials(cls, v):
        if not v or not v.strip():
            raise ValueError('RMS credentials cannot be empty')
        return v.strip()


class SetupWizardResponse(BaseModel):
    """Response schema for setup wizard completion"""
    
    success: bool
    message: str
    access_token: Optional[str] = None
    redirect_url: Optional[str] = "/"

