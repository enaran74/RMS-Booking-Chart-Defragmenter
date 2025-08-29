"""
Lightweight RMS Client for Web Application
Provides basic RMS API integration without heavy dependencies like pandas/numpy
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.core import config as app_config

logger = logging.getLogger(__name__)

class LightweightRMSClient:
    """Lightweight RMS client for basic API operations without pandas dependencies"""
    
    def __init__(self):
        self.base_url = "https://restapi12.rmscloud.com"
        self.session = requests.Session()
        self.token = None
        self.token_expiry = None
        self._last_debug_message = None
        self._current_property_code = None # Track current property for WebSocket
        
        # CRITICAL: Match original RMS client date constraints exactly (31 days from today)
        today = datetime.now().date()
        self.constraint_start_date = today
        self.constraint_end_date = today + timedelta(days=31)
        
        logger.info(f"Initialized LightweightRMSClient - Analysis period: {self.constraint_start_date} to {self.constraint_end_date}")
    
    def _send_websocket_debug(self, message: str, message_type: str = "rms_http_debug"):
        """Send debug message to WebSocket if available"""
        if not self._current_property_code:
            return
            
        try:
            from app.core.websocket_manager import websocket_manager
            from datetime import datetime
            import asyncio
            
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Send debug message without progress value to avoid interfering with progress bar
                debug_message = {
                    "type": "debug_message",
                    "step": message_type,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                asyncio.create_task(websocket_manager.broadcast_to_property(
                    self._current_property_code,
                    debug_message
                ))
        except Exception as e:
            pass  # WebSocket debug message failed
            pass
    
    async def _send_websocket_progress(self, message: str, progress: float, step_name: str = "rms_analysis"):
        """Send progress update with both debug message AND progress value"""
        if not self._current_property_code:
            logger.warning(f"WebSocket progress skipped - no property code set")
            return
            
        try:
            from app.core.websocket_manager import websocket_manager
            
            # Send progress update with actual progress value
            await websocket_manager.send_progress_update(
                self._current_property_code,
                step_name,
                message,
                progress=progress
            )
            
        except Exception as e:
            logger.error(f"❌ WebSocket progress message failed: {e}")
    
    def authenticate(self) -> bool:
        """Authenticate with RMS API using credentials from settings"""
        logger.info("Authenticating with RMS API")
        
        try:
            auth_payload = {
                "AgentId": app_config.settings.AGENT_ID,
                "AgentPassword": app_config.settings.AGENT_PASSWORD,
                "ClientId": app_config.settings.CLIENT_ID,
                "ClientPassword": app_config.settings.CLIENT_PASSWORD,
                "UseTrainingDatabase": app_config.settings.USE_TRAINING_DB,
                "ModuleType": ["distribution"]
            }
            
            logger.info(f"Auth URL: {self.base_url}/authToken")
            response = self.session.post(f"{self.base_url}/authToken", json=auth_payload)
            
            logger.info(f"RMS API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # RMS API returns token directly, not wrapped in a success field
                if data.get('token'):
                    self.token = data.get('token')
                    
                    # Parse expiry date from response if available, otherwise assume 1 hour
                    expiry_str = data.get('expiryDate')
                    if expiry_str:
                        try:
                            self.token_expiry = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            self.token_expiry = datetime.now() + timedelta(hours=1)
                    else:
                        self.token_expiry = datetime.now() + timedelta(hours=1)
                    
                    # Set RMS API token header for future requests (RMS uses 'authtoken', not 'Authorization')
                    self.session.headers.update({
                        'authtoken': self.token,
                        'Content-Type': 'application/json'
                    })
                    
                    logger.info(f"RMS API authentication successful. Token expires: {self.token_expiry}")
                    logger.info(f"Available properties: {len(data.get('allowedProperties', []))}")
                    return True
                else:
                    logger.error(f"RMS API authentication failed - no token in response: {data}")
                    return False
            else:
                logger.error(f"RMS API authentication failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"RMS API authentication error: {e}")
            return False
    
    def _is_token_valid(self) -> bool:
        """Check if the current token is still valid"""
        if not self.token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token"""
        if not self._is_token_valid():
            logger.info("Token expired or missing, re-authenticating")
            return self.authenticate()
        return True
    
    def get_property_reservations(self, property_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get reservations for a specific property using correct RMS API endpoint"""
        if not self._ensure_authenticated():
            logger.error("Failed to authenticate with RMS API")
            return None
        
        try:
            logger.info(f"Fetching reservations for property {property_id}")
            
            # First get categories for this property (required for reservation search)
            categories = self.get_property_categories(property_id)
            if not categories:
                logger.warning(f"No categories found for property {property_id}")
                return []
            
            category_ids = [cat['id'] for cat in categories]
            logger.info(f"Using {len(category_ids)} category IDs for reservation filtering")
            
            # Use constraint dates (31 days from today, matching original RMS client)
            start_date = self.constraint_start_date
            end_date = self.constraint_end_date
            
            # Build reservation search payload (matching original RMS client)
            search_payload = {
                "propertyIds": [property_id],
                "categoryIds": category_ids,
                "arriveFrom": "2000-01-01 00:00:00",
                "arriveTo": f"{end_date} 23:59:59",
                "departFrom": f"{start_date} 00:00:00",
                "departTo": "2050-12-31 23:59:59",
                "listOfStatus": [
                    "unconfirmed", "confirmed", "arrived", "maintenance", 
                    "quote", "ownerOccupied", "pencil", "departed"
                ],
                "includeGroupMasterReservations": "ExcludeGroupMasters",
                "includeInterconnecterSiblings": False,
                "includeRoomMoveHeaders": False,
                "limitProjectedRevenueToDateRange": False
            }
            
            params = {
                'limit': 2000,
                'modelType': 'full',
                'offset': 0
            }
            
            # Use correct RMS API endpoint for reservations search
            url = f"{self.base_url}/reservations/search"
            self._send_websocket_debug(f"🌐 POST {url} (propertyIds=[{property_id}], {len(category_ids)} categories, limit=2000)")
            
            response = self.session.post(url, json=search_payload, params=params)
            
            if response.status_code == 200:
                reservations = response.json()  # Direct list response
                logger.info(f"Retrieved {len(reservations)} reservations for property {property_id}")
                self._send_websocket_debug(f"📡 Reservations Response: {response.status_code} → {len(reservations)} reservations")
                return reservations
            else:
                logger.error(f"Failed to fetch reservations: {response.status_code} - {response.text}")
                self._send_websocket_debug(f"❌ Reservations API failed: {response.status_code} - {response.text[:100]}...")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching reservations: {e}")
            return None
    
    def get_property_reservations_with_categories(self, property_id: int, categories: List[Dict]) -> Optional[List[Dict[str, Any]]]:
        """Get reservations for a specific property using pre-fetched categories (avoids duplicate API call)"""
        if not self._ensure_authenticated():
            logger.error("Failed to authenticate with RMS API")
            return None
        
        try:
            logger.info(f"Fetching reservations for property {property_id} with pre-fetched categories")
            
            if not categories:
                logger.warning(f"No categories provided for property {property_id}")
                return []
            
            category_ids = [cat['id'] for cat in categories]
            logger.info(f"Using {len(category_ids)} category IDs for reservation filtering")
            
            # Use constraint dates (31 days from today, matching original RMS client)
            start_date = self.constraint_start_date
            end_date = self.constraint_end_date
            
            # Build reservation search payload (matching original RMS client)
            search_payload = {
                "propertyIds": [property_id],
                "categoryIds": category_ids,
                "arriveFrom": "2000-01-01 00:00:00",
                "arriveTo": f"{end_date} 23:59:59",
                "departFrom": f"{start_date} 00:00:00",
                "departTo": "2050-12-31 23:59:59",
                "listOfStatus": [
                    "unconfirmed", "confirmed", "arrived", "maintenance", 
                    "quote", "ownerOccupied", "pencil", "departed"
                ],
                "includeGroupMasterReservations": "ExcludeGroupMasters",
                "includeInterconnecterSiblings": False,
                "includeRoomMoveHeaders": False,
                "limitProjectedRevenueToDateRange": False
            }
            
            params = {
                'limit': 2000,
                'modelType': 'full',
                'offset': 0
            }
            
            # Use correct RMS API endpoint for reservations search
            url = f"{self.base_url}/reservations/search"
            self._send_websocket_debug(f"🌐 POST {url} (propertyIds=[{property_id}], {len(category_ids)} categories, limit=2000)")
            
            response = self.session.post(url, json=search_payload, params=params)
            
            if response.status_code == 200:
                reservations = response.json()  # Direct list response
                logger.info(f"Retrieved {len(reservations)} reservations for property {property_id}")
                self._send_websocket_debug(f"📡 Reservations Response: {response.status_code} → {len(reservations)} reservations")
                return reservations
            else:
                logger.error(f"Failed to fetch reservations: {response.status_code} - {response.text}")
                self._send_websocket_debug(f"❌ Reservations API failed: {response.status_code} - {response.text[:100]}...")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching reservations: {e}")
            return None
    
    def get_property_categories(self, property_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get categories for a specific property (required for other API calls)"""
        if not self._ensure_authenticated():
            logger.error("Failed to authenticate with RMS API")
            return None
        
        try:
            logger.info(f"Fetching categories for property {property_id}")
            
            params = {
                'propertyId': property_id,
                'modelType': 'Full',
                'limit': 2000
            }
            
            # Debug: Log the request details
            url = f"{self.base_url}/categories"
            logger.info(f"🌐 RMS API Request: GET {url}")
            logger.info(f"📋 Request params: {params}")
            logger.info(f"🔑 Request headers: authtoken={self.token[:20]}...")
            
            # Send debug info about the request
            self._send_websocket_debug(f"🌐 POST {url} (propertyId={property_id}, modelType=Full, limit=2000)")
            
            response = self.session.get(url, params=params)
            
            # Debug: Log the response details
            logger.info(f"📡 RMS API Response: {response.status_code}")
            logger.info(f"📄 Response size: {len(response.text)} chars")
            
            # Send debug info about the response
            if response.status_code == 200:
                all_categories = response.json()
                self._send_websocket_debug(f"📡 Categories Response: {response.status_code} → {len(all_categories)} total categories")
            else:
                self._send_websocket_debug(f"❌ Categories API failed: {response.status_code} - {response.text[:100]}...")
            
            if response.status_code == 200:
                all_categories = response.json()
                logger.info(f"📊 Raw categories received: {len(all_categories)}")
                
                # Filter: inactive=false AND availableToIbe=true (matching original client)
                filtered_categories = [
                    cat for cat in all_categories 
                    if not cat.get('inactive', False) and cat.get('availableToIbe', False)
                ]
                
                logger.info(f"✅ Retrieved {len(filtered_categories)} active categories for property {property_id}")
                return filtered_categories
            else:
                logger.error(f"❌ Failed to fetch categories: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"💥 Error fetching categories: {e}")
            return None

    def get_property_units(self, property_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get units/areas for a specific property using correct RMS API endpoint"""
        if not self._ensure_authenticated():
            logger.error("Failed to authenticate with RMS API")
            return None
        
        try:
            logger.info(f"Fetching areas/units for property {property_id}")
            
            params = {
                'propertyId': property_id,
                'modelType': 'Full',
                'limit': 2000
            }
            
            # Use correct RMS API endpoint for areas/units
            url = f"{self.base_url}/areas"
            self._send_websocket_debug(f"🌐 GET {url} (propertyId={property_id}, modelType=Full, limit=2000)")
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                all_areas = response.json()
                
                # Filter: inactive=false AND statisticsStatus=true (matching original client)
                filtered_areas = [
                    area for area in all_areas 
                    if not area.get('inactive', False) and area.get('statisticsStatus', False)
                ]
                
                logger.info(f"Retrieved {len(filtered_areas)} active areas/units for property {property_id}")
                self._send_websocket_debug(f"📡 Areas Response: {response.status_code} → {len(all_areas)} total → {len(filtered_areas)} active areas")
                return filtered_areas
            else:
                logger.error(f"Failed to fetch areas/units: {response.status_code} - {response.text}")
                self._send_websocket_debug(f"❌ Areas API failed: {response.status_code} - {response.text[:100]}...")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching areas/units: {e}")
            return None
    
    def get_property_areas_for_moves(self, property_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get areas/units for a specific property optimized for move operations (uses lite model)"""
        if not self._ensure_authenticated():
            logger.error("Failed to authenticate with RMS API")
            return None
        
        try:
            logger.info(f"Fetching areas for move operations - property {property_id}")
            
            params = {
                'propertyId': property_id,
                'modelType': 'full',  # Use full model to get complete area names for exact matching
                'limit': 2000,  # Increased limit to get all areas
                'inactive': 'false'  # Only get active areas to avoid inactive/old units
            }
            
            # Use correct RMS API endpoint for areas
            url = f"{self.base_url}/areas"
            self._send_websocket_debug(f"🌐 GET {url} (propertyId={property_id}, modelType=full, limit=2000, inactive=false)")
            
            # Enhanced logging: Log the complete request details
            logger.info(f"🔍 AREAS API REQUEST DETAILS:")
            logger.info(f"   URL: {url}")
            logger.info(f"   Params: {params}")
            logger.info(f"   Headers: {dict(self.session.headers)}")
            
            response = self.session.get(url, params=params)
            
            # Enhanced logging: Log the complete response details
            logger.info(f"🔍 AREAS API RESPONSE DETAILS:")
            logger.info(f"   Status Code: {response.status_code}")
            logger.info(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                areas = response.json()
                logger.info(f"   Response Body Length: {len(response.text)} characters")
                logger.info(f"   Number of Areas Returned: {len(areas)}")
                
                # Log first 5 complete area objects for analysis
                logger.info(f"🔍 FIRST 5 AREAS FROM RMS API:")
                for i, area in enumerate(areas[:5]):
                    logger.info(f"   Area {i+1}: {area}")
                
                # Log specific CALI-103 related areas
                cali_103_areas = [area for area in areas if 'CALI-103' in str(area.get('name', ''))]
                logger.info(f"🔍 ALL CALI-103 RELATED AREAS:")
                for area in cali_103_areas:
                    logger.info(f"   CALI-103 Area: {area}")
                
                logger.info(f"✅ Retrieved {len(areas)} areas for property {property_id} (full model)")
                self._send_websocket_debug(f"📡 Areas Response: {response.status_code} → {len(areas)} areas for move operations")
                return areas
            else:
                logger.error(f"❌ Failed to fetch areas: {response.status_code} - {response.text}")
                self._send_websocket_debug(f"❌ Areas API failed: {response.status_code} - {response.text[:100]}...")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching areas for moves: {e}")
            self._send_websocket_debug(f"❌ Areas fetch error: {str(e)}")
            return None
    
    def create_area_name_to_id_mapping(self, areas: List[Dict[str, Any]]) -> Dict[str, int]:
        """Create a mapping from area names to area IDs for move operations
        
        Args:
            areas: List of area objects from RMS API (lite model)
            
        Returns:
            Dict mapping area names to area IDs, e.g. {"Room 3": 7, "Room 5": 9}
        """
        if not areas:
            logger.warning("No areas provided for name-to-ID mapping")
            return {}
        
        name_to_id = {}
        for area in areas:
            area_name = area.get('name')
            area_id = area.get('id')
            if area_name and area_id:
                name_to_id[area_name] = area_id
            else:
                logger.warning(f"Skipping area with missing name or id: {area}")
        
        logger.info(f"Created area name-to-ID mapping with {len(name_to_id)} entries")
        self._send_websocket_debug(f"🗺️ Created area mapping: {len(name_to_id)} area names → IDs")
        
        # Enhanced Debug: Log all area mappings for troubleshooting
        logger.info("📋 Complete area name-to-ID mapping:")
        for name, area_id in sorted(name_to_id.items()):
            logger.info(f"   '{name}' → {area_id}")
        
        # Debug: Log first few mappings for WebSocket
        for i, (name, area_id) in enumerate(list(name_to_id.items())[:5]):
            logger.debug(f"   Area mapping {i}: '{name}' → {area_id}")
        
        return name_to_id
    
    async def analyze_simple_defragmentation(self, property_id: int, property_code: str = "UNKNOWN") -> List[Dict[str, Any]]:
        """Perform proper defragmentation analysis using sophisticated algorithms"""
        print(f"🚨🚨🚨 ANALYZE_SIMPLE_DEFRAGMENTATION CALLED FOR {property_id} 🚨🚨🚨")
        logger.info(f"🚨 ANALYZE_SIMPLE_DEFRAGMENTATION CALLED FOR {property_id}")
        logger.info(f"Starting proper defragmentation analysis for property {property_id}")
        
        # Set current property for WebSocket debugging
        self._current_property_code = property_code
        
        # Send debug info about starting RMS API calls
        self._send_websocket_debug(f"📡 Starting RMS API calls for property {property_id} ({property_code})")
        
        # Get data from RMS API with detailed debugging
        logger.info(f"🚀 STEP A: About to call _send_websocket_progress for categories...")
        self._send_websocket_debug(f"💥 BEFORE PROGRESS CALL: About to call progress for categories...")
        try:
            await self._send_websocket_progress(f"🌐 Step 1/6: Fetching categories for property {property_id}...", 70.0, "rms_categories")
            self._send_websocket_debug(f"💥 AFTER PROGRESS CALL: Progress call succeeded!")
        except Exception as e:
            self._send_websocket_debug(f"💥 PROGRESS FAILED: {str(e)}")
        logger.info(f"🚀 STEP B: About to call get_property_categories...")
        categories = self.get_property_categories(property_id)
        logger.info(f"🚀 STEP C: get_property_categories returned: {len(categories) if categories else 0} categories")
        if categories:
            await self._send_websocket_progress(f"✅ Found {len(categories)} active categories", 72.0, "rms_categories")
        else:
            logger.error(f"🚀 EARLY EXIT: No categories found for property {property_id}")
            self._send_websocket_debug(f"❌ No categories found for property {property_id}")
            return []
        
        await self._send_websocket_progress(f"📡 Step 2/6: Fetching reservations for property {property_id}...", 75.0, "rms_reservations")
        reservations = self.get_property_reservations_with_categories(property_id, categories)
        if reservations:
            await self._send_websocket_progress(f"✅ Found {len(reservations)} reservations", 78.0, "rms_reservations")
        else:
            self._send_websocket_debug(f"❌ No reservations found for property {property_id}")
            return []
        
        await self._send_websocket_progress(f"🏠 Step 3/6: Fetching units/areas for property {property_id}...", 80.0, "rms_units")
        units = self.get_property_units(property_id)
        if units:
            await self._send_websocket_progress(f"✅ Found {len(units)} active units/areas", 82.0, "rms_units")
        else:
            self._send_websocket_debug(f"❌ No units found for property {property_id}")
            return []
        
        # Send detailed debug info about what we received  
        categories_count = len(categories or [])
        reservations_count = len(reservations or [])
        units_count = len(units or [])
        
        self._send_websocket_debug(f"📊 RMS API Results: {categories_count} categories, {reservations_count} reservations, {units_count} units")
        
        if not reservations or not units:
            logger.warning(f"Insufficient data for analysis: {len(reservations or [])} reservations, {len(units or [])} units")
            return []
        
        # Import and use the ORIGINAL defrag analyzer (exactly matching the CLI script)
        try:
            logger.info(f"🔄 STEP 1: Starting ORIGINAL analyzer import...")
            
            # Add the root directory to sys.path to import original modules
            import sys
            import os
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            logger.info(f"🔄 STEP 2: Root dir calculated as: {root_dir}")
            
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)
                logger.info(f"🔄 STEP 3: Added root_dir to sys.path")
            
            logger.info(f"🔄 STEP 4: About to import DefragmentationAnalyzer...")
            from defrag_analyzer import DefragmentationAnalyzer
            logger.info(f"🔄 STEP 5: Successfully imported DefragmentationAnalyzer")
            
            await self._send_websocket_progress(f"🔄 Step 4/6: Converting RMS data to analysis format...", 85.0, "data_conversion")
            analyzer = DefragmentationAnalyzer()
            
            # Convert our API data to the format expected by the original analyzer
            reservations_df = self._convert_to_original_dataframe_format(reservations, 'reservations', property_id)
            units_df = self._convert_to_original_dataframe_format(units, 'units', property_id)
            
            await self._send_websocket_progress(f"✅ Data conversion complete: {len(reservations_df)} reservations, {len(units_df)} units ready for analysis", 87.0, "data_conversion")
            
            # DETAILED DEBUGGING - Compare with original script data counts
            logger.info(f"WEB APP DATA COUNTS:")
            logger.info(f"  Raw reservations from API: {len(reservations)}")
            logger.info(f"  Raw units from API: {len(units)}")
            logger.info(f"  Converted reservations DataFrame: {len(reservations_df)}")
            logger.info(f"  Converted units DataFrame: {len(units_df)}")
            logger.info(f"  Analysis period: {self.constraint_start_date} to {self.constraint_end_date}")
            
            self._send_websocket_debug(f"📊 COMPARISON: WEB APP has {len(reservations_df)} reservations, {len(units_df)} units")
            self._send_websocket_debug(f"📊 ORIGINAL had 775 reservations, 314 units - DIFFERENCE: {len(reservations_df)-775} reservations, {len(units_df)-314} units")
            
            # CRITICAL DEBUGGING - Check category distribution
            if len(reservations_df) > 0:
                logger.info(f"WEB APP Reservations DataFrame columns: {list(reservations_df.columns)}")
                
                # CRITICAL: Check category distribution (this is the root cause!)
                if 'Category' in reservations_df.columns:
                    category_counts = reservations_df['Category'].value_counts()
                    unique_categories = reservations_df['Category'].nunique()
                    logger.info(f"🎯 CATEGORY ANALYSIS:")
                    logger.info(f"   - Unique categories: {unique_categories}")
                    logger.info(f"   - Category distribution: {dict(category_counts.head(10))}")
                    logger.info(f"   - Expected: 16 categories (from original)")
                    
                    self._send_websocket_debug(f"🎯 CRITICAL: WEB APP has {unique_categories} categories vs ORIGINAL's 16")
                    
                    if unique_categories == 1:
                        single_category = reservations_df['Category'].iloc[0]
                        logger.error(f"❌ FOUND THE BUG: All reservations have same category: '{single_category}'")
                        self._send_websocket_debug(f"❌ BUG: All reservations grouped into: '{single_category}'")
                else:
                    logger.error("❌ CRITICAL: No 'Category' column in reservations DataFrame!")
                
                logger.info(f"WEB APP Reservations DataFrame sample: {reservations_df.head(2).to_dict()}")
            
            if len(units_df) > 0:
                logger.info(f"WEB APP Units DataFrame columns: {list(units_df.columns)}")
                if 'Category' in units_df.columns:
                    unit_categories = units_df['Category'].value_counts()
                    logger.info(f"WEB APP Unit categories: {dict(unit_categories)}")
                logger.info(f"WEB APP Units DataFrame sample: {units_df.head(2).to_dict()}")
            
            # Show category analysis before starting
            if 'Category' in reservations_df.columns:
                category_counts = reservations_df['Category'].value_counts()
                unique_categories = len(category_counts)
                self._send_websocket_debug(f"📊 Found {unique_categories} room categories to analyze")
                for i, (category, count) in enumerate(category_counts.head(5).items()):
                    self._send_websocket_debug(f"   Category {i+1}: {category} ({count} reservations)")
                if len(category_counts) > 5:
                    self._send_websocket_debug(f"   ... and {len(category_counts)-5} more categories")
            
            # Run the ORIGINAL analysis with exact constraint dates
            await self._send_websocket_progress(f"🧠 Step 5/6: Running defragmentation analysis...", 90.0, "analysis_running")
            await self._send_websocket_progress(f"📅 Analysis period: {self.constraint_start_date} to {self.constraint_end_date}", 92.0, "analysis_running")
            
            logger.info(f"🔍 Calling DefragmentationAnalyzer.analyze_defragmentation()...")
            logger.info(f"   - reservations_df shape: {reservations_df.shape}")
            logger.info(f"   - units_df shape: {units_df.shape}")
            logger.info(f"   - constraint_start_date: {self.constraint_start_date}")
            logger.info(f"   - constraint_end_date: {self.constraint_end_date}")
            
            suggestions = analyzer.analyze_defragmentation(
                reservations_df, units_df, self.constraint_start_date, self.constraint_end_date
            )
            
            await self._send_websocket_progress(f"✅ Analysis complete! Found {len(suggestions) if suggestions else 0} optimization opportunities", 95.0, "analysis_complete")
            
            logger.info(f"🎯 DefragmentationAnalyzer returned {len(suggestions) if suggestions else 0} raw suggestions")
            if suggestions:
                logger.info(f"   Sample suggestion keys: {list(suggestions[0].keys()) if len(suggestions) > 0 else 'None'}")
                for i, suggestion in enumerate(suggestions[:3]):
                    logger.info(f"   Raw suggestion {i}: {suggestion}")
            else:
                logger.warning(f"❌ DefragmentationAnalyzer returned empty suggestions list")
            
            await self._send_websocket_progress(f"🔄 Step 6/6: Converting suggestions to web format...", 97.0, "format_conversion")
            
            logger.info(f"Generated {len(suggestions)} ORIGINAL defragmentation suggestions for property {property_id}")
            
            # Convert ORIGINAL suggestions to expected format
            # Original analyzer returns list of dictionaries with specific keys
            converted_suggestions = []
            for idx, suggestion in enumerate(suggestions):
                # DEBUG: Log the actual suggestion structure

                if idx < 3:  # Only show first 3 in debug output to avoid spam
                    self._send_websocket_debug(f"🔍 Processing suggestion {idx+1}: {suggestion.get('Surname', 'Unknown')} from {suggestion.get('Current_Unit', 'Unknown')} to {suggestion.get('Suggested_Unit', 'Unknown')}")
                
                converted_suggestion = {
                    "current_unit": suggestion.get('Current_Unit', ''),
                    "target_unit": suggestion.get('Suggested_Unit', ''),
                    "guest_name": suggestion.get('Surname', 'Guest'),
                    "check_in": suggestion.get('Arrive_Date', '') or suggestion.get('Arrival_Date', ''),
                    "check_out": suggestion.get('Depart_Date', '') or suggestion.get('Departure_Date', ''),
                    "strategic_importance": suggestion.get('Strategic_Importance', 'Medium'),
                    "score": int(float(suggestion.get('Improvement_Score', 0)) * 100),
                    "reason": suggestion.get('Reason', 'Defragmentation optimization'),
                    "reservation_id": str(suggestion.get('Reservation_No', '')),
                    "category": suggestion.get('Category', 'Unknown'),
                    "nights_freed": suggestion.get('Nights_Freed', 1),
                    "sequential_order": suggestion.get('Sequential_Order', f"{idx + 1}")
                }
                
                # DEBUG: Log the converted suggestion

                self._send_websocket_debug(f"🔄 Converted suggestion {idx}: guest={converted_suggestion['guest_name']}, from={converted_suggestion['current_unit']}, to={converted_suggestion['target_unit']}")
                
                converted_suggestions.append(converted_suggestion)
            
            await self._send_websocket_progress(f"✅ Analysis Complete! Generated {len(converted_suggestions)} move suggestions", 100.0, "complete")
            if converted_suggestions:
                best_score = max(s.get('score', 0) for s in converted_suggestions)
                avg_score = sum(s.get('score', 0) for s in converted_suggestions) / len(converted_suggestions)
                await self._send_websocket_progress(f"📊 Quality metrics: Best score: {best_score}, Average score: {avg_score:.1f}", 100.0, "complete")
            
            return converted_suggestions
            
        except Exception as e:
            logger.error(f"Error in ORIGINAL defragmentation analysis: {e}")
            self._send_websocket_debug(f"❌ CRITICAL ERROR: Original analysis failed: {str(e)}")
            
            # NO FALLBACK - raise the error so user sees the real issue
            raise Exception(f"Defragmentation analysis failed: {str(e)}. Please check server configuration.")
    
    def _convert_to_original_dataframe_format(self, data_list, data_type, property_id=None):
        """Convert RMS API data to pandas DataFrame format expected by original analyzer"""
        try:
            import pandas as pd
            
            # CRITICAL: Build category lookup ONCE at method level for both reservations AND units
            category_lookup = {}
            if property_id:
                try:
                    categories = self.get_property_categories(property_id)
                    category_lookup = {cat['id']: cat['name'] for cat in categories} if categories else {}
                    logger.info(f"🔧 METHOD-LEVEL category lookup with {len(category_lookup)} categories")
                    # Debug: Show first few category mappings
                    for i, (cat_id, cat_name) in enumerate(list(category_lookup.items())[:5]):
                        logger.info(f"   Category {i}: {cat_id} → '{cat_name}'")
                except Exception as e:
                    logger.warning(f"Could not build category lookup: {e}")
                    category_lookup = {}
            
            if data_type == 'reservations':
                # Convert reservation data to match ORIGINAL analyzer DataFrame structure
                # CRITICAL: Apply same area filtering as original RMS client
                
                # Build area lookup for filtering (only active areas with statistics)
                area_lookup = {}
                filtered_out_count = 0
                
                if property_id:
                    # Get filtered areas (active + statisticsStatus=true) like original
                    try:
                        units = self.get_property_units(property_id)
                        if units:
                            area_lookup = {
                                unit['id']: unit['name'] 
                                for unit in units 
                                if not unit.get('inactive', False) and unit.get('statisticsStatus', True)
                            }
                            logger.info(f"Built area lookup with {len(area_lookup)} active areas for filtering")
                        else:
                            logger.warning("No units data available for area filtering")
                    except Exception as e:
                        logger.warning(f"Could not build area lookup: {e}")
                
                # If no area lookup available, include all reservations (fallback)
                if not area_lookup:
                    for res in data_list:
                        area_id = res.get('areaId')
                        area_name = res.get('areaName')
                        if area_id and area_name:
                            area_lookup[area_id] = area_name
                
                df_data = []
                
                for res in data_list:
                    # CRITICAL: Filter out reservations for excluded areas (matching original)
                    area_id = res.get('areaId')
                    if area_id and area_id not in area_lookup:
                        filtered_out_count += 1
                        continue
                    # CRITICAL: Apply same preprocessing as original RMS client
                    arrival_formatted = self._format_date_for_analysis(res.get('arrivalDate', ''))
                    departure_formatted = self._format_date_for_analysis(res.get('departureDate', ''))
                    nights_calculated = self._calculate_nights(res.get('arrivalDate', ''), res.get('departureDate', ''))
                    status_mapped = self._map_reservation_status(res.get('status', ''))
                    
                    # CRITICAL FIX: Use EXACT SAME logic as original RMS client
                    # Original code gets categoryId from reservation and looks it up in category_lookup
                    area_name = res.get('areaName', '')
                    category_id = res.get('categoryId')  # This is the key field!
                    
                    # Look up category name exactly like original
                    category_name = category_lookup.get(category_id, 'Unknown Category')
                    
                    # CRITICAL DEBUG: Log category mapping for first few reservations
                    if len(df_data) < 5:  # Log first 5 reservations
                        logger.info(f"🔍 ORIGINAL LOGIC: Reservation {len(df_data)}: categoryId={category_id} → category='{category_name}'")
                    
                    df_data.append({
                        'Res No': str(res.get('id', '')),  # CRITICAL: Original expects 'Res No'
                        'Unit/Site': area_name,  # CRITICAL: Original expects 'Unit/Site'
                        'Category': category_name,  # CRITICAL: Fixed category mapping
                        'Arrive': arrival_formatted,  # CRITICAL: d/m/yyyy H:MM format
                        'Depart': departure_formatted,  # CRITICAL: d/m/yyyy H:MM format
                        'Surname': res.get('guestSurname', ''),  # CRITICAL: Original expects 'Surname'
                        'Status': status_mapped,  # CRITICAL: Mapped status
                        'Nights': str(nights_calculated),  # CRITICAL: Calculated nights as string
                        'Fixed': str(res.get('fixedRes', False)),  # CRITICAL: Missing 'Fixed' field
                        'propertyId': res.get('propertyId'),
                        'guestGiven': res.get('guestGiven')
                    })
                
                # Log filtering results like original
                df = pd.DataFrame(df_data)
                if filtered_out_count > 0:
                    logger.info(f"Filtered out {filtered_out_count} reservations for excluded areas")
                    self._send_websocket_debug(f"📋 Filtered out {filtered_out_count} reservations for excluded areas")
                logger.info(f"Built {len(df)} reservation records after area filtering")
                return df
            
            elif data_type == 'units':
                # Convert unit/area data to match original DataFrame structure
                df_data = []
                for unit in data_list:
                    # CRITICAL: Use category lookup for units too (units don't have categoryName, only categoryId)
                    unit_category_id = unit.get('categoryId')
                    unit_category_name = category_lookup.get(unit_category_id, 'Unknown Category')
                    
                    df_data.append({
                        'id': unit.get('id'),
                        'propertyId': unit.get('propertyId'),
                        'Unit/Site': unit.get('name'),  # CRITICAL: Original analyzer expects 'Unit/Site'
                        'Category': unit_category_name,  # CRITICAL: Must map categoryId to categoryName
                        'inactive': unit.get('inactive', False),
                        'statisticsStatus': unit.get('statisticsStatus', True)
                    })
                return pd.DataFrame(df_data)
            
            else:
                logger.error(f"Unknown data type for DataFrame conversion: {data_type}")
                return pd.DataFrame()
                
        except ImportError:
            logger.error("pandas not available for DataFrame conversion")
            return []
        except Exception as e:
            logger.error(f"Error converting {data_type} to DataFrame: {e}")
            return []
    
    def _format_date_for_analysis(self, api_date: str) -> str:
        """Format API date for analysis (d/m/yyyy H:MM format) - matching original RMS client"""
        if not api_date:
            return ''
        
        try:
            if 'T' in api_date:
                dt = datetime.fromisoformat(api_date.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(api_date, '%Y-%m-%d %H:%M:%S')
            
            return dt.strftime('%d/%m/%Y %H:%M')
            
        except Exception as e:
            logger.error(f"Date format error for '{api_date}': {e}")
            return api_date
    
    def _calculate_nights(self, arrival_date: str, departure_date: str) -> int:
        """Calculate number of nights between arrival and departure - matching original RMS client"""
        try:
            if not arrival_date or not departure_date:
                return 0
            
            if 'T' in arrival_date:
                arrive_dt = datetime.fromisoformat(arrival_date.replace('Z', '+00:00'))
            else:
                arrive_dt = datetime.strptime(arrival_date, '%Y-%m-%d %H:%M:%S')
                
            if 'T' in departure_date:
                depart_dt = datetime.fromisoformat(departure_date.replace('Z', '+00:00'))
            else:
                depart_dt = datetime.strptime(departure_date, '%Y-%m-%d %H:%M:%S')
            
            nights = (depart_dt.date() - arrive_dt.date()).days
            return max(0, nights)
            
        except Exception as e:
            logger.error(f"Night calculation error: {e}")
            return 0
    
    def _map_reservation_status(self, api_status: str) -> str:
        """Map RMS API status to expected values - matching original RMS client"""
        if not api_status:
            return 'Unknown'
        
        status_mapping = {
            'confirmed': 'Confirmed',
            'unconfirmed': 'Unconfirmed', 
            'arrived': 'Arrived',
            'departed': 'Departed',
            'maintenance': 'Maintenance',
            'quote': 'Quote',
            'ownerOccupied': 'Owner Occupied',
            'pencil': 'Pencil'
        }
        
        return status_mapping.get(api_status.lower(), api_status.title())
    
    def _map_strategic_importance_level(self, importance_score: float) -> str:
        """Map numeric strategic importance to level"""
        if importance_score >= 0.7:
            return "High"
        elif importance_score >= 0.4:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_nights_freed(self, check_in: str, check_out: str) -> int:
        """Calculate nights freed by a move"""
        try:
            if check_in and check_out:
                nights = (datetime.strptime(check_out[:10], '%Y-%m-%d') - datetime.strptime(check_in[:10], '%Y-%m-%d')).days
                return max(1, nights - 1)
        except:
            pass
        return 1
    
    def _simple_fallback_analysis(self, reservations: List[Dict], units: List[Dict], property_id: int) -> List[Dict[str, Any]]:
        """Simple fallback analysis if proper analysis fails"""
        logger.info(f"Running simple fallback analysis for property {property_id}")
        
        suggestions = []
        analysis_limit = min(10, len(reservations))
        
        for i, reservation in enumerate(reservations[:analysis_limit]):
            # Extract basic reservation info
            guest_name = f"{reservation.get('firstName', 'Guest')} {reservation.get('lastName', str(i+1))}"
            current_unit = reservation.get('unitCode', f'Unit{i+1}')
            # Use the correct RMS API field names for dates
            check_in = reservation.get('arrivalDate', '') or reservation.get('checkIn', datetime.now().strftime('%Y-%m-%d'))
            check_out = reservation.get('departureDate', '') or reservation.get('checkOut', (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'))
            
            # Format the dates properly (remove time if present)
            if check_in and 'T' in check_in:
                check_in = check_in.split('T')[0]
            elif check_in and ' ' in check_in:
                check_in = check_in.split(' ')[0]
            
            if check_out and 'T' in check_out:
                check_out = check_out.split('T')[0]
            elif check_out and ' ' in check_out:
                check_out = check_out.split(' ')[0]
            
            logger.info(f"📋 Reservation {i+1}: {guest_name} in {current_unit} from {check_in} to {check_out}")
            
            # Multiple optimization rules
            try:
                nights = (datetime.strptime(check_out[:10], '%Y-%m-%d') - datetime.strptime(check_in[:10], '%Y-%m-%d')).days
                logger.info(f"🌙 Reservation {i+1}: {nights} nights")
                
                # Rule 1: Short stays (< 4 nights) could be moved to premium units
                # Rule 2: Long stays (> 7 nights) could be moved to standard units  
                # Rule 3: Mid-week arrivals could be optimized
                
                should_suggest = False
                suggestion_reason = ""
                importance = "Low"
                
                if nights < 4 and len(units) > 1:
                    should_suggest = True
                    suggestion_reason = f"Short stay ({nights} nights) - move to premium unit to free space for longer bookings"
                    importance = "Medium" if nights <= 2 else "Low"
                    logger.info(f"💡 Short stay optimization opportunity: {nights} nights")
                elif nights > 7 and len(units) > 1:
                    should_suggest = True  
                    suggestion_reason = f"Long stay ({nights} nights) - move to standard unit, save premium for shorter stays"
                    importance = "Medium"
                    logger.info(f"💡 Long stay optimization opportunity: {nights} nights")
                elif nights >= 4 and nights <= 7 and len(units) > 5:  # Only if many units available
                    should_suggest = True
                    suggestion_reason = f"Mid-length stay ({nights} nights) - optimize unit placement for better revenue"
                    importance = "Low"
                    logger.info(f"💡 Mid-length stay optimization opportunity: {nights} nights")
                
                if should_suggest:
                    # Find an alternative unit
                    alternative_unit = None
                    for unit in units:
                        if unit.get('unitCode') != current_unit:
                            alternative_unit = unit.get('unitCode', f'AltUnit{i}')
                            break
                    
                    if alternative_unit:
                        # Calculate score based on nights and importance
                        base_score = 50
                        if nights <= 2:
                            base_score = 80  # High priority for very short stays
                        elif nights > 7:
                            base_score = 70  # High priority for long stays
                        elif nights >= 4:
                            base_score = 60  # Medium priority for mid-length stays
                        
                        suggestion = {
                            "from_unit": current_unit,
                            "to_unit": alternative_unit,
                            "guest": guest_name,
                            "check_in": check_in[:10],
                            "check_out": check_out[:10],
                            "strategic_importance": importance,
                            "score": base_score,
                            "reason": suggestion_reason,
                            "reservation_id": reservation.get('id'),
                            "nights": nights
                        }
                        suggestions.append(suggestion)
                        logger.info(f"✅ Added suggestion: Move {guest_name} from {current_unit} to {alternative_unit}")
                        
                        if len(suggestions) >= 10:  # Increased limit to 10 suggestions
                            logger.info(f"🔄 Reached suggestion limit of 10, stopping analysis")
                            break
                            
            except Exception as e:
                logger.warning(f"Error processing reservation {i}: {e}")
                continue
        
        logger.info(f"Generated {len(suggestions)} simple move suggestions for property {property_id}")
        return suggestions
