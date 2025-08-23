"""
Setup Wizard API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import logging
import asyncio
from pathlib import Path

from app.core.database import get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.property import Property
from app.schemas.setup_wizard import SetupWizardData, SetupWizardResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/check-setup-required")
async def check_setup_required(db: Session = Depends(get_db)):
    """Check if first-time setup is required (no admin users exist)"""
    try:
        admin_count = db.query(User).filter(User.is_admin == True).count()
        
        return {
            "setup_required": admin_count == 0,
            "admin_count": admin_count
        }
    except Exception as error:
        logger.error(f"Error checking setup requirement: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check setup requirement"
        )


@router.post("/complete", response_model=SetupWizardResponse)
async def complete_setup_wizard(
    setup_data: SetupWizardData,
    db: Session = Depends(get_db)
):
    """Complete the first-time setup wizard"""
    
    try:
        logger.info("Starting setup wizard completion...")
        
        # Check if setup is actually required
        admin_count = db.query(User).filter(User.is_admin == True).count()
        if admin_count > 0:
            raise HTTPException(
                status_code=400,
                detail="Setup has already been completed. Admin users exist."
            )
        
        # 1. Create admin user
        logger.info(f"Creating admin user: {setup_data.adminUsername}")
        
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == setup_data.adminUsername).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail=f"Username '{setup_data.adminUsername}' already exists"
            )
        
        # Create the admin user
        admin_user = User(
            username=setup_data.adminUsername,
            password_hash=get_password_hash(setup_data.adminPassword),
            email=setup_data.adminEmail or f"{setup_data.adminUsername}@dhpsystems.com",
            first_name="Administrator",
            last_name=setup_data.adminUsername,
            is_admin=True,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"Admin user created successfully: {admin_user.username}")
        
        # 2. Load properties into database from RMS API
        logger.info("Loading properties from RMS API into database...")
        try:
            properties_loaded = await load_properties_into_database(setup_data, db)
            if properties_loaded > 0:
                logger.info(f"Successfully loaded {properties_loaded} properties into database")
            else:
                logger.warning("No properties were loaded into database - this may affect functionality")
        except Exception as e:
            logger.warning(f"Failed to load properties from RMS API: {e}")
            # Don't fail setup if property loading fails - it can be done later
        
        # 3. Generate comprehensive .env file
        logger.info("Generating environment configuration...")
        env_content = generate_complete_env_file(setup_data)
        
        # Write to multiple locations for compatibility
        env_paths = [
            "/app/.env",  # Container location
            "/opt/defrag-app/.env"  # Host shared location (if mounted)
        ]
        
        for env_path in env_paths:
            try:
                write_env_file(env_path, env_content)
                logger.info(f"Environment file written to: {env_path}")
            except Exception as e:
                logger.warning(f"Could not write to {env_path}: {e}")
        
        # 4. Create access token for immediate login
        access_token = create_access_token(data={"sub": admin_user.username})
        
        logger.info("Setup wizard completed successfully")
        
        return SetupWizardResponse(
            success=True,
            message="Setup completed successfully! Redirecting to application...",
            access_token=access_token,
            redirect_url="/"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as error:
        logger.error(f"Setup wizard completion failed: {error}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Setup failed: {str(error)}"
        )


def generate_complete_env_file(setup_data: SetupWizardData) -> str:
    """Generate a complete .env file with smart defaults"""
    
    # Determine USE_TRAINING_DB based on system mode
    use_training_db = "true" if setup_data.systemMode == "training" else "false"
    
    # Build the complete environment configuration
    env_content = f"""# ==============================================================================
# RMS Booking Chart Defragmenter - Configuration
# ==============================================================================
# Generated by Setup Wizard on first installation
# You can modify these settings in the Setup page of the web interface

# ==============================================================================
# RMS API CREDENTIALS
# ==============================================================================
AGENT_ID={setup_data.agentId}
AGENT_PASSWORD={setup_data.agentPassword}
CLIENT_ID={setup_data.clientId}
CLIENT_PASSWORD={setup_data.clientPassword}

# ==============================================================================
# DATABASE CONFIGURATION (Web App)
# ==============================================================================
DB_HOST=defrag-postgres
DB_PORT=5432
DB_NAME=defrag_db
DB_USER=defrag_user
DB_PASSWORD=DefragDB2024!

# ==============================================================================
# WEB APPLICATION CONFIGURATION
# ==============================================================================
WEB_APP_PORT=8000
WEB_APP_HOST=0.0.0.0
SECRET_KEY=dhp-defrag-secret-key-{setup_data.adminUsername}-2024
JWT_SECRET_KEY=dhp-jwt-secret-{setup_data.adminUsername}-2024

# Property data refresh interval (hours)
PROPERTY_REFRESH_INTERVAL_HOURS=1

# ==============================================================================
# ANALYSIS CONFIGURATION
# ==============================================================================
TARGET_PROPERTIES={setup_data.targetProperties}
USE_TRAINING_DB={use_training_db}

# ==============================================================================
# EMAIL CONFIGURATION (Disabled by default)
# ==============================================================================
ENABLE_EMAILS=false
SEND_CONSOLIDATED_EMAIL=false
CONSOLIDATED_EMAIL_RECIPIENT=operations@discoveryparks.com.au

# SMTP Configuration (configure in Setup page if needed)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL={setup_data.adminEmail or f"{setup_data.adminUsername}@dhpsystems.com"}
SENDER_DISPLAY_NAME=DHP Defragmentation System
APP_PASSWORD=configure_in_setup_page
TEST_RECIPIENT={setup_data.adminEmail or f"{setup_data.adminUsername}@dhpsystems.com"}

# ==============================================================================
# SCHEDULING CONFIGURATION
# ==============================================================================
CRON_SCHEDULE=0 2 * * *
ENABLE_CRON=true

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================
LOG_LEVEL=INFO
LOG_DIR=/app/logs

# ==============================================================================
# OUTPUT CONFIGURATION
# ==============================================================================
OUTPUT_DIR=/app/output

# ==============================================================================
# CONTAINER CONFIGURATION
# ==============================================================================
TZ={setup_data.timezone}
CONTAINER_USER=appuser
CONTAINER_GROUP=appuser

# ==============================================================================
# HEALTH CHECK CONFIGURATION
# ==============================================================================
HEALTH_CHECK_INTERVAL=30s
HEALTH_CHECK_TIMEOUT=10s
HEALTH_CHECK_RETRIES=3

# ==============================================================================
# BACKUP CONFIGURATION
# ==============================================================================
BACKUP_RETENTION_DAYS=30
BACKUP_ENABLED=true

# ==============================================================================
# CORS CONFIGURATION (Web App)
# ==============================================================================
CORS_ORIGINS=["http://localhost:8000","http://127.0.0.1:8000","http://0.0.0.0:8000"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET","POST","PUT","DELETE","OPTIONS"]
CORS_ALLOW_HEADERS=["*"]
"""
    
    return env_content


def write_env_file(file_path: str, content: str) -> None:
    """Write environment file to specified path"""
    try:
        path = Path(file_path)
        
        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Environment file written successfully to: {file_path}")
        
    except Exception as error:
        logger.error(f"Failed to write environment file to {file_path}: {error}")
        raise


class RMSTestRequest(BaseModel):
    """Request model for testing RMS API connection"""
    agentId: str
    agentPassword: str
    clientId: str
    clientPassword: str
    systemMode: str = "training"

@router.post("/test-rms-connection")
async def test_rms_connection_wizard(test_data: RMSTestRequest):
    """Test RMS API connection during setup wizard"""
    try:
        logger.info("Testing RMS API connection from setup wizard")
        
        # Extract credentials from request
        agent_id = test_data.agentId
        agent_password = test_data.agentPassword
        client_id = test_data.clientId
        client_password = test_data.clientPassword
        use_training_db = test_data.systemMode == "training"
        
        # Validate required credentials
        if not all([agent_id, agent_password, client_id, client_password]):
            return {
                "success": False,
                "message": "Missing required RMS credentials",
                "details": {
                    "error": "All RMS credentials are required for testing"
                }
            }
        
        # Test RMS API connection
        import requests
        
        base_url = "https://restapi12.rmscloud.com"
        
        auth_payload = {
            "AgentId": agent_id,
            "AgentPassword": agent_password,
            "ClientId": client_id,
            "ClientPassword": client_password,
            "UseTrainingDatabase": use_training_db,
            "ModuleType": ["distribution"]
        }
        
        logger.info(f"Testing authentication with RMS API at {base_url}/authToken")
        
        # Test authentication
        response = requests.post(f"{base_url}/authToken", json=auth_payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            
            if token:
                # Test a simple API call to verify the token works
                headers = {
                    'authtoken': token,
                    'Content-Type': 'application/json'
                }
                
                # Try to fetch properties to verify full API access
                try:
                    properties_response = requests.get(
                        f"{base_url}/properties",
                        headers=headers,
                        params={'modelType': 'Full', 'limit': 10},
                        timeout=30
                    )
                    
                    if properties_response.status_code == 200:
                        properties = properties_response.json()
                        properties_count = len(properties) if properties else 0
                        
                        database_type = "Training Database" if use_training_db else "Live Database"
                        
                        return {
                            "success": True,
                            "message": f"🎉 RMS API connection successful! Connected to {database_type}.",
                            "details": {
                                "authentication": "✅ Successful",
                                "database_mode": database_type,
                                "properties_accessible": f"✅ {properties_count} properties found",
                                "token_expiry": data.get('expiryDate', 'Not specified'),
                                "api_endpoint": base_url,
                                "ready_for_setup": True
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "message": "Authentication successful but failed to access RMS data",
                            "details": {
                                "authentication": "✅ Successful",
                                "api_access": f"❌ Failed ({properties_response.status_code})",
                                "error": properties_response.text[:200] if properties_response.text else "Unknown error"
                            }
                        }
                        
                except requests.exceptions.Timeout:
                    return {
                        "success": False,
                        "message": "Authentication successful but RMS API is not responding",
                        "details": {
                            "authentication": "✅ Successful",
                            "api_access": "❌ Timeout",
                            "error": "RMS API did not respond within 30 seconds"
                        }
                    }
                except Exception as api_error:
                    return {
                        "success": False,
                        "message": "Authentication successful but failed to verify API access",
                        "details": {
                            "authentication": "✅ Successful", 
                            "api_access": "❌ Error",
                            "error": str(api_error)[:200]
                        }
                    }
            else:
                return {
                    "success": False,
                    "message": "RMS API authentication failed - no token received",
                    "details": {
                        "authentication": "❌ Failed",
                        "error": "No authentication token in response",
                        "response": str(data)[:200] if data else "Empty response"
                    }
                }
        else:
            error_message = "Unknown error"
            try:
                error_data = response.json()
                error_message = error_data.get('message', str(error_data))
            except:
                error_message = response.text[:200] if response.text else f"HTTP {response.status_code}"
            
            return {
                "success": False,
                "message": f"❌ RMS API authentication failed (HTTP {response.status_code})",
                "details": {
                    "authentication": "❌ Failed",
                    "status_code": response.status_code,
                    "error": error_message,
                    "credentials_check": {
                        "agent_id": f"✅ Provided ({agent_id})" if agent_id else "❌ Missing",
                        "agent_password": "✅ Provided" if agent_password else "❌ Missing",
                        "client_id": f"✅ Provided ({client_id})" if client_id else "❌ Missing",
                        "client_password": "✅ Provided" if client_password else "❌ Missing"
                    }
                }
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "RMS API connection timeout - server not responding",
            "details": {
                "error": "Connection timeout after 30 seconds",
                "possible_causes": [
                    "RMS API server is down",
                    "Network connectivity issues",
                    "Firewall blocking the connection"
                ]
            }
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Cannot connect to RMS API server",
            "details": {
                "error": "Connection failed",
                "api_endpoint": "https://restapi12.rmscloud.com",
                "possible_causes": [
                    "No internet connection",
                    "RMS API server is unreachable",
                    "DNS resolution issues"
                ]
            }
        }
    except Exception as error:
        logger.error(f"Error testing RMS connection in setup wizard: {error}")
        return {
            "success": False,
            "message": f"RMS API test failed: {str(error)}",
            "details": {
                "error": str(error)[:300],
                "type": type(error).__name__
            }
        }


def extract_property_info_wizard(property_data: dict) -> dict:
    """Extract property code, name, and RMS ID from RMS property data (wizard version)"""
    try:
        # Extract RMS property ID (this is the key field we need!)
        rms_property_id = None
        if 'id' in property_data and property_data['id']:
            rms_property_id = int(property_data['id'])
        
        # Try different possible field names for property code
        property_code = None
        for code_field in ['code', 'propertyCode', 'Code', 'PropertyCode']:
            if code_field in property_data and property_data[code_field]:
                property_code = str(property_data[code_field]).strip()
                break
        
        # Try different possible field names for property name
        property_name = None
        for name_field in ['name', 'propertyName', 'Name', 'PropertyName']:
            if name_field in property_data and property_data[name_field]:
                property_name = str(property_data[name_field]).strip()
                break
        
        # Extract active status - RMS API returns 'inactive' field, convert to 'is_active'
        is_active = True  # Default to active
        if 'inactive' in property_data:
            is_active = not property_data['inactive']  # Convert inactive to is_active
        
        if property_code and property_name and rms_property_id:
            # Clean property code by removing trailing hyphens
            clean_code = property_code.rstrip('- _').strip()
            
            return {
                'code': clean_code,
                'name': property_name,
                'rms_id': rms_property_id,
                'is_active': is_active
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting property info: {e}")
        return None


async def load_properties_into_database(setup_data: SetupWizardData, db: Session) -> int:
    """Load properties from RMS API into database during setup wizard completion"""
    try:
        # Create a test request data object for fetching properties
        from pydantic import BaseModel
        
        test_request = RMSTestRequest(
            agentId=setup_data.agentId,
            agentPassword=setup_data.agentPassword,
            clientId=setup_data.clientId,
            clientPassword=setup_data.clientPassword,
            systemMode=setup_data.systemMode
        )
        
        # Fetch properties from RMS
        properties_response = await fetch_rms_properties_wizard(test_request)
        
        if not properties_response.get("success") or not properties_response.get("properties"):
            logger.warning("Failed to fetch properties from RMS API during setup")
            return 0
        
        properties_data = properties_response["properties"]
        properties_loaded = 0
        
        # Load each property into the database
        for prop_data in properties_data:
            try:
                # Check if property already exists by code
                existing_property = db.query(Property).filter(
                    Property.property_code == prop_data['code']
                ).first()
                
                if existing_property:
                    # Update existing property with RMS ID and details
                    existing_property.property_name = prop_data['name']
                    existing_property.rms_property_id = prop_data['rms_id']
                    existing_property.is_active = prop_data['is_active']
                    logger.info(f"Updated existing property: {prop_data['code']} - {prop_data['name']}")
                else:
                    # Create new property
                    new_property = Property(
                        property_code=prop_data['code'],
                        property_name=prop_data['name'],
                        rms_property_id=prop_data['rms_id'],
                        is_active=prop_data['is_active']
                    )
                    db.add(new_property)
                    logger.info(f"Added new property: {prop_data['code']} - {prop_data['name']} (RMS ID: {prop_data['rms_id']})")
                
                properties_loaded += 1
                
            except Exception as e:
                logger.error(f"Error loading property {prop_data.get('code', 'unknown')}: {e}")
                continue
        
        # Commit all property changes
        db.commit()
        
        logger.info(f"Successfully loaded {properties_loaded} properties into database")
        return properties_loaded
        
    except Exception as e:
        logger.error(f"Error loading properties into database: {e}")
        db.rollback()
        return 0


@router.post("/fetch-rms-properties")
async def fetch_rms_properties_wizard(test_data: RMSTestRequest):
    """Fetch properties from RMS API using provided credentials during setup wizard"""
    try:
        logger.info("Fetching properties from RMS API during setup wizard")
        
        # Validate required credentials
        if not all([test_data.agentId, test_data.agentPassword, test_data.clientId, test_data.clientPassword]):
            return {
                "success": False,
                "message": "Missing required RMS credentials",
                "properties": []
            }
        
        # Use the same RMS connection logic as the main service
        import requests
        
        base_url = "https://restapi12.rmscloud.com"
        use_training_db = test_data.systemMode == "training"
        
        auth_payload = {
            "AgentId": test_data.agentId,
            "AgentPassword": test_data.agentPassword,
            "ClientId": test_data.clientId,
            "ClientPassword": test_data.clientPassword,
            "UseTrainingDatabase": use_training_db,
            "ModuleType": ["distribution"]
        }
        
        # Step 1: Authenticate
        auth_response = requests.post(f"{base_url}/authToken", json=auth_payload, timeout=30)
        
        if auth_response.status_code != 200:
            return {
                "success": False,
                "message": "Failed to authenticate with RMS API",
                "properties": []
            }
        
        auth_data = auth_response.json()
        token = auth_data.get('token')
        
        if not token:
            return {
                "success": False,
                "message": "No authentication token received",
                "properties": []
            }
        
        headers = {
            'authtoken': token,
            'Content-Type': 'application/json'
        }
        
        # Step 2: Fetch properties using the same logic as RMSService
        endpoints_to_try = [
            "/properties",
            "/api/v1/properties", 
            "/property"
        ]
        
        params = {
            'modelType': 'Full',
            'limit': 2000
        }
        
        properties_data = []
        
        for endpoint in endpoints_to_try:
            logger.info(f"Trying RMS endpoint: {endpoint}")
            try:
                response = requests.get(f"{base_url}{endpoint}", headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    raw_properties = response.json()
                    if raw_properties:
                        logger.info(f"Successfully fetched {len(raw_properties)} properties from {endpoint}")
                        
                        # Extract property information using the same logic as RMSService
                        for prop_data in raw_properties:
                            property_info = extract_property_info_wizard(prop_data)
                            if property_info:
                                properties_data.append(property_info)
                        
                        break
                else:
                    logger.warning(f"Endpoint {endpoint} failed: Status {response.status_code}")
            except Exception as e:
                logger.warning(f"Error trying endpoint {endpoint}: {e}")
                continue
        
        if not properties_data:
            return {
                "success": False,
                "message": "No properties could be fetched from RMS API",
                "properties": []
            }
        
        # Sort properties by code for consistent display
        properties_data.sort(key=lambda x: x['code'])
        
        logger.info(f"Successfully extracted {len(properties_data)} valid properties")
        
        return {
            "success": True,
            "message": f"Successfully fetched {len(properties_data)} properties from RMS",
            "properties": properties_data
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "Connection timeout to RMS API",
            "properties": []
        }
    except Exception as error:
        logger.error(f"Error fetching RMS properties: {error}")
        return {
            "success": False,
            "message": f"Error fetching properties: {str(error)}",
            "properties": []
        }
