"""
RMS Service for the Web Application
Handles RMS API integration and property management
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.property import Property
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

class RMSService:
    """Service for interacting with RMS API and managing properties"""
    
    def __init__(self):
        self.base_url = "https://restapi12.rmscloud.com"
        self.session = requests.Session()
        self.token = None
        self.token_expiry = None
        self.last_property_refresh = None
        
    def authenticate(self) -> bool:
        """Authenticate with RMS API"""
        logger.info("authenticate method called")
        logger.info(f"Using agent ID: {settings.AGENT_ID}")
        logger.info(f"Using client ID: {settings.CLIENT_ID}")
        logger.info(f"Using training DB: {settings.USE_TRAINING_DB}")
        logger.info(f"Base URL: {self.base_url}")
        
        try:
            auth_payload = {
                "AgentId": settings.AGENT_ID,
                "AgentPassword": settings.AGENT_PASSWORD,
                "ClientId": settings.CLIENT_ID,
                "ClientPassword": settings.CLIENT_PASSWORD,
                "UseTrainingDatabase": settings.USE_TRAINING_DB,
                "ModuleType": ["distribution"]
            }
            
            logger.info("Authenticating with RMS API")
            logger.info(f"Auth URL: {self.base_url}/authToken")
            response = self.session.post(f"{self.base_url}/authToken", json=auth_payload)
            
            logger.info(f"RMS API response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"RMS API response data keys: {list(data.keys()) if data else 'None'}")
                self.token = data.get('token')
                self.token_expiry = data.get('expiryDate')
                logger.info(f"Token received: {'Yes' if self.token else 'No'}")
                logger.info(f"Token expiry: {self.token_expiry}")
                
                if self.token:
                    self.session.headers.update({
                        'authtoken': self.token,
                        'Content-Type': 'application/json'
                    })
                    logger.info("RMS API authentication successful")
                    return True
                else:
                    logger.error("No token in RMS API response")
                    
            logger.error(f"RMS API authentication failed: Status {response.status_code}")
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    logger.error(f"Error response data: {error_data}")
                except:
                    logger.error(f"Error response text: {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"RMS API authentication error: {e}")
            return False
    
    def _is_token_valid(self) -> bool:
        """Check if the current token is still valid"""
        logger.info(f"_is_token_valid called - token: {'Yes' if self.token else 'No'}, expiry: {self.token_expiry}")
        if not self.token or not self.token_expiry:
            logger.info("No token or expiry date")
            return False
        
        try:
            expiry_date = datetime.fromisoformat(self.token_expiry.replace('Z', '+00:00'))
            is_valid = datetime.now(expiry_date.tzinfo) < expiry_date
            logger.info(f"Token expiry: {expiry_date}, is_valid: {is_valid}")
            return is_valid
        except Exception as e:
            logger.error(f"Error checking token validity: {e}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token"""
        logger.info("_ensure_authenticated called")
        if not self._is_token_valid():
            logger.info("Token not valid, calling authenticate()")
            return self.authenticate()
        logger.info("Token is valid")
        return True
    
    def fetch_properties(self) -> List[Dict]:
        """Fetch properties from RMS API"""
        if not self._ensure_authenticated():
            logger.error("Failed to authenticate with RMS API")
            return []
        
        try:
            # Try different possible endpoints
            endpoints_to_try = [
                "/properties",
                "/api/v1/properties", 
                "/property"
            ]
            
            params = {
                'modelType': 'Full',
                'limit': 2000
            }
            
            for endpoint in endpoints_to_try:
                logger.info(f"Trying RMS endpoint: {endpoint}")
                response = self.session.get(f"{self.base_url}{endpoint}", params=params)
                
                if response.status_code == 200:
                    properties = response.json()
                    if properties:
                        logger.info(f"Successfully fetched {len(properties)} properties from {endpoint}")
                        return properties
                else:
                    logger.warning(f"Endpoint {endpoint} failed: Status {response.status_code}")
            
            logger.error("All RMS property endpoints failed")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching properties from RMS API: {e}")
            return []
    
    def _clean_property_code(self, code: str) -> str:
        """Clean property code by removing trailing hyphens and normalizing"""
        if not code:
            return ""
        return code.rstrip('- _').strip()
    
    def _extract_property_info(self, property_data: Dict) -> Optional[Dict]:
        """Extract property code, name, and active status from RMS property data"""
        try:
            # Try different possible field names for property code
            property_code = None
            for code_field in ['code', 'propertyCode', 'Code', 'PropertyCode']:
                if code_field in property_data and property_data[code_field]:
                    property_code = str(property_data[code_field])
                    break
            
            # Try different possible field names for property name
            property_name = None
            for name_field in ['name', 'propertyName', 'Name', 'PropertyName']:
                if name_field in property_data and property_data[name_field]:
                    property_name = str(property_data[name_field])
                    break
            
            # Extract active status - RMS API returns 'inactive' field, convert to 'is_active'
            is_active = True  # Default to active
            if 'inactive' in property_data:
                is_active = not property_data['inactive']  # Convert inactive to is_active
            
            if property_code and property_name:
                return {
                    'code': self._clean_property_code(property_code),
                    'name': property_name.strip(),
                    'is_active': is_active
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting property info: {e}")
            return None
    
    def refresh_properties_in_database(self, db: Session = None) -> bool:
        """Refresh properties in the database from RMS API"""
        logger.info("refresh_properties_in_database called")
        logger.info(f"db parameter: {db}")
        
        # Create our own database session if none provided
        own_session = False
        if db is None:
            logger.info("No db session provided, creating new one")
            from app.core.database import SessionLocal
            db = SessionLocal()
            own_session = True
        else:
            logger.info("Using provided db session")
            
        try:
            # Check if we need to refresh (not more than once per hour)
            if self.last_property_refresh:
                time_since_refresh = datetime.now() - self.last_property_refresh
                if time_since_refresh < timedelta(hours=settings.PROPERTY_REFRESH_INTERVAL_HOURS):
                    logger.info("Properties were recently refreshed, skipping refresh")
                    return True
            
            logger.info("Refreshing properties from RMS API")
            
            # Fetch properties from RMS API
            logger.info("Calling fetch_properties()")
            rms_properties = self.fetch_properties()
            logger.info(f"fetch_properties returned {len(rms_properties) if rms_properties else 0} properties")
            
            if not rms_properties:
                logger.error("No properties received from RMS API")
                return False
            
            # Extract and clean property information
            valid_properties = []
            for prop in rms_properties:
                property_info = self._extract_property_info(prop)
                if property_info:
                    valid_properties.append(property_info)
            
            logger.info(f"Extracted {len(valid_properties)} valid properties from RMS API")
            
            # Update database
            properties_updated = 0
            properties_created = 0
            
            for prop_info in valid_properties:
                # Check if property already exists
                existing_property = db.query(Property).filter(
                    Property.property_code == prop_info['code']
                ).first()
                
                if existing_property:
                    # Update existing property
                    updated = False
                    if existing_property.property_name != prop_info['name']:
                        existing_property.property_name = prop_info['name']
                        updated = True
                    if existing_property.is_active != prop_info['is_active']:
                        existing_property.is_active = prop_info['is_active']
                        updated = True
                    if updated:
                        properties_updated += 1
                else:
                    # Create new property
                    new_property = Property(
                        property_code=prop_info['code'],
                        property_name=prop_info['name'],
                        is_active=prop_info['is_active']
                    )
                    db.add(new_property)
                    properties_created += 1
            
            # Commit changes
            db.commit()
            
            # Update refresh timestamp
            self.last_property_refresh = datetime.now()
            
            logger.info(f"Property refresh complete: {properties_created} created, {properties_updated} updated")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing properties in database: {e}")
            try:
                db.rollback()
            except:
                pass  # Ignore rollback errors
            return False
        finally:
            # Close our own session if we created it
            if own_session:
                try:
                    db.close()
                except:
                    pass  # Ignore close errors
    
    def get_properties_from_database(self, db: Session, force_refresh: bool = False) -> List[Property]:
        """Get properties from database, optionally forcing a refresh"""
        if force_refresh:
            # Pass the existing db session to avoid transaction conflicts
            self.refresh_properties_in_database(db)
        
        # Get all properties from database
        properties = db.query(Property).order_by(Property.property_code).all()
        return properties
    
    def get_property_by_code(self, db: Session, property_code: str) -> Optional[Property]:
        """Get a specific property by its code"""
        return db.query(Property).filter(Property.property_code == property_code).first()

# Global RMS service instance
rms_service = RMSService()
