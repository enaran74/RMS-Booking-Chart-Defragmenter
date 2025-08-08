#!/usr/bin/env python3
"""
RMS API Client
Handles authentication and data retrieval from RMS API
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from utils import get_logger

class RMSClient:
    def __init__(self, agent_id: str, agent_password: str, client_id: str, client_password: str, use_training_db: bool = False):
        """Initialize RMS API client with provided credentials"""
        
        # Initialize logging
        self.logger = get_logger()
        self.logger.log_function_entry("RMSClient.__init__", 
                                     agent_id=agent_id, 
                                     client_id=client_id, 
                                     use_training_db=use_training_db)
        
        # RMS credentials passed as parameters
        self.agent_id = agent_id
        self.agent_password = agent_password
        self.client_id = client_id
        self.client_password = client_password
        self.use_training_db = use_training_db
        self.base_url = "https://restapi12.rmscloud.com"
        self.timezone = "Australia/Adelaide"
        
        # Dynamic analysis date constraints (next 31 days from today)
        today = datetime.now().date()
        self.constraint_start_date = today
        self.constraint_end_date = today + timedelta(days=31)
        
        # API session management
        self.session = requests.Session()
        self.token = None
        self.token_expiry = None
        self.all_properties = []
        
        # Comprehensive caching system
        self._categories_cache = {}  # property_id -> categories
        self._areas_cache = {}       # property_id -> areas
        self._property_metadata_cache = {}  # property_id -> metadata
        self._cache_timestamps = {}  # property_id -> last_fetch_time
        self._cache_ttl = 300  # Cache TTL in seconds (5 minutes)
        
        # Endpoint monitoring system
        self._endpoint_stats = {}  # property_id -> endpoint statistics
        
        # State code mapping for holiday integration
        self.STATE_COUNTRY_MAPPING = {
            'VIC': 'AU', 'TAS': 'AU', 'ACT': 'AU', 'NSW': 'AU',
            'QLD': 'AU', 'NT': 'AU', 'SA': 'AU', 'WA': 'AU'
        }
        
        self.logger.info(f"RMSClient initialized - Analysis period: {self.constraint_start_date} to {self.constraint_end_date}")
        self.logger.log_function_exit("RMSClient.__init__")

    def authenticate(self) -> bool:
        """Authenticate with RMS API and discover available properties"""
        start_time = time.time()
        self.logger.log_function_entry("authenticate")
        
        print(f"\n🔐 AUTHENTICATING WITH RMS API")
        print("=" * 40)
        
        auth_payload = {
            "AgentId": self.agent_id,
            "AgentPassword": self.agent_password,
            "ClientId": self.client_id,
            "ClientPassword": self.client_password,
            "UseTrainingDatabase": self.use_training_db,
            "ModuleType": ["distribution"]
        }
        
        try:
            self.logger.info("Authenticating with RMS API")
            print("📡 Connecting to RMS...")
            response = self.session.post(f"{self.base_url}/authToken", json=auth_payload)
            
            self.logger.log_api_call("/authToken", "POST", str(response.status_code), len(response.content))
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.token_expiry = data.get('expiryDate')
                
                if self.token:
                    self.session.headers.update({
                        'authtoken': self.token,
                        'Content-Type': 'application/json'
                    })
                    self.logger.info("Authentication successful")
                    print(f"✅ Authentication successful!")
                    print(f"🔑 Token expires: {self.token_expiry}")
                    
                    # Get properties from allowedProperties first (for reference)
                    allowed_properties = data.get('allowedProperties', [])
                    self.logger.log_data_summary("Allowed properties", len(allowed_properties))
                    print(f"🏢 Found {len(allowed_properties)} allowed properties in auth response")
                    
                    # Now fetch detailed properties using /properties endpoint
                    self.logger.info("Fetching detailed property information")
                    print("📡 Fetching detailed property information...")
                    self.all_properties = self._fetch_properties_from_endpoint()
                    
                    if self.all_properties:
                        self.logger.log_data_summary("Detailed properties retrieved", len(self.all_properties))
                        print(f"✅ Retrieved {len(self.all_properties)} detailed properties")
                    else:
                        self.logger.warning("No properties from /properties endpoint, using allowedProperties")
                        print("⚠️  No properties from /properties endpoint, using allowedProperties")
                        self.all_properties = allowed_properties
                    
                    duration = time.time() - start_time
                    self.logger.log_performance_metric("Authentication", duration)
                    self.logger.log_function_exit("authenticate", True)
                    return True
                    
            self.logger.error(f"Authentication failed: Status {response.status_code}")
            print(f"❌ Authentication failed: Status {response.status_code}")
            return False
            
        except Exception as e:
            self.logger.log_error_with_context(e, "Authentication")
            print(f"❌ Authentication error: {e}")
            return False

    def _fetch_properties_from_endpoint(self) -> List[Dict]:
        """Fetch properties using the /properties endpoint with full model type"""
        try:
            # Try different possible endpoints with full model type
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
                print(f"   📡 Trying endpoint: {endpoint} with modelType=Full")
                response = self.session.get(f"{self.base_url}{endpoint}", params=params)
                
                if response.status_code == 200:
                    properties = response.json()
                    if properties:
                        print(f"   ✅ Success with {endpoint}: Found {len(properties)} properties")
                        return properties
                else:
                    print(f"   ❌ {endpoint} failed: Status {response.status_code}")
            
            # If all endpoints fail, return empty list
            print("   ⚠️  All property endpoints failed")
            return []
            
        except Exception as e:
            print(f"   ❌ Error fetching properties: {e}")
            return []

    def get_all_properties(self) -> List[Dict]:
        """Return list of all discovered properties"""
        return self.all_properties
    
    def clear_cache(self):
        """Clear all cached data"""
        self._categories_cache.clear()
        self._areas_cache.clear()
        self._property_metadata_cache.clear()
        self._cache_timestamps.clear()
        print("🗑️  Cache cleared")
    
    def clear_property_cache(self, property_id: int):
        """Clear cached data for a specific property"""
        self._categories_cache.pop(property_id, None)
        self._areas_cache.pop(property_id, None)
        self._property_metadata_cache.pop(property_id, None)
        self._cache_timestamps.pop(property_id, None)
        print(f"🗑️  Cache cleared for property {property_id}")
    
    def _is_cache_valid(self, property_id: int) -> bool:
        """Check if cached data for property is still valid"""
        if property_id not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[property_id]
        current_time = datetime.now().timestamp()
        return (current_time - cache_time) < self._cache_ttl
    
    def _update_cache_timestamp(self, property_id: int):
        """Update cache timestamp for property"""
        self._cache_timestamps[property_id] = datetime.now().timestamp()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'categories_cache_size': len(self._categories_cache),
            'areas_cache_size': len(self._areas_cache),
            'metadata_cache_size': len(self._property_metadata_cache),
            'total_cached_properties': len(self._cache_timestamps),
            'cache_ttl_seconds': self._cache_ttl
        }
    
    def get_endpoint_stats(self) -> Dict:
        """Get endpoint statistics for all properties"""
        return self._endpoint_stats
    
    def _record_endpoint_data(self, property_id: int, property_name: str, endpoint: str, data_count: int, limit: int = 2000):
        """Record endpoint data volume for monitoring"""
        if property_id not in self._endpoint_stats:
            self._endpoint_stats[property_id] = {
                'property_name': property_name,
                'endpoints': {}
            }
        
        self._endpoint_stats[property_id]['endpoints'][endpoint] = {
            'data_count': data_count,
            'limit': limit,
            'usage_percent': (data_count / limit) * 100 if limit > 0 else 0,
            'near_limit': data_count >= (limit * 0.9)  # 90% of limit
        }
    
    def print_endpoint_summary(self):
        """Print comprehensive endpoint usage summary table"""
        if not self._endpoint_stats:
            print("\n📊 No endpoint data recorded")
            return
        
        print(f"\n📊 ENDPOINT USAGE SUMMARY")
        print("=" * 120)
        
        # Table header
        print(f"{'Property':<20} {'Code':<8} {'Categories':<12} {'Areas':<8} {'Reservations':<12} {'Status'}")
        print("-" * 120)
        
        # Sort properties by name for better readability
        sorted_properties = sorted(self._endpoint_stats.items(), key=lambda x: x[1]['property_name'])
        
        for property_id, stats in sorted_properties:
            property_name = stats['property_name']
            endpoints = stats['endpoints']
            
            # Get property code (try to find it from the property name or use ID)
            property_code = f"ID:{property_id}"
            
            # Extract data counts and limits
            categories_data = endpoints.get('categories', {})
            areas_data = endpoints.get('areas', {})
            reservations_data = endpoints.get('reservations', {})
            
            categories_count = categories_data.get('data_count', 0)
            areas_count = areas_data.get('data_count', 0)
            reservations_count = reservations_data.get('data_count', 0)
            
            categories_limit = categories_data.get('limit', 1000)
            areas_limit = areas_data.get('limit', 1000)
            reservations_limit = reservations_data.get('limit', 1000)
            
            # Format as fractions
            categories_fraction = f"{categories_count}/{categories_limit}"
            areas_fraction = f"{areas_count}/{areas_limit}"
            reservations_fraction = f"{reservations_count}/{reservations_limit}"
            
            # Determine status
            status_parts = []
            if endpoints.get('categories', {}).get('near_limit', False):
                status_parts.append("CAT-LIMIT")
            if endpoints.get('areas', {}).get('near_limit', False):
                status_parts.append("AREA-LIMIT")
            if endpoints.get('reservations', {}).get('near_limit', False):
                status_parts.append("RES-LIMIT")
            
            status = ", ".join(status_parts) if status_parts else "OK"
            
            # Color coding for status
            if "LIMIT" in status:
                status = f"⚠️  {status}"
            else:
                status = f"✅ {status}"
            
            print(f"{property_name[:19]:<20} {property_code:<8} {categories_fraction:<12} {areas_fraction:<8} {reservations_fraction:<12} {status}")
        
        # Summary statistics
        print("-" * 120)
        self._print_endpoint_summary_stats()
    
    def _print_endpoint_summary_stats(self):
        """Print summary statistics for endpoint usage"""
        total_properties = len(self._endpoint_stats)
        properties_near_limit = 0
        max_categories = 0
        max_areas = 0
        max_reservations = 0
        
        for stats in self._endpoint_stats.values():
            endpoints = stats['endpoints']
            
            # Check for near-limit properties
            if any(endpoint.get('near_limit', False) for endpoint in endpoints.values()):
                properties_near_limit += 1
            
            # Track maximums
            max_categories = max(max_categories, endpoints.get('categories', {}).get('data_count', 0))
            max_areas = max(max_areas, endpoints.get('areas', {}).get('data_count', 0))
            max_reservations = max(max_reservations, endpoints.get('reservations', {}).get('data_count', 0))
        
        print(f"📈 SUMMARY STATISTICS:")
        print(f"   Total Properties Analyzed: {total_properties}")
        print(f"   Properties Near Limits: {properties_near_limit}")
        print(f"   Maximum Categories: {max_categories}")
        print(f"   Maximum Areas: {max_areas}")
        print(f"   Maximum Reservations: {max_reservations}")
        
        # Recommendations
        if properties_near_limit > 0:
            print(f"\n⚠️  RECOMMENDATIONS:")
            print(f"   {properties_near_limit} properties are approaching API limits")
            print(f"   Consider increasing limits for affected endpoints")
        else:
            print(f"\n✅ All properties are well within API limits")

    def fetch_inventory_data(self, property_id: int, property_name: str) -> pd.DataFrame:
        """Fetch live inventory data from RMS API for specified property with caching"""
        print(f"\n📦 FETCHING INVENTORY DATA")
        print("=" * 40)
        
        # Get categories (with caching)
        print("📋 Fetching categories...")
        categories = self._get_categories(property_id, property_name)
        if not categories:
            print("❌ No categories found")
            return pd.DataFrame()
        
        # Get areas/units (with caching)
        print("🏠 Fetching areas/units...")
        areas = self._get_areas(property_id, property_name)
        if not areas:
            print("❌ No areas found")
            return pd.DataFrame()
        
        # Build inventory DataFrame
        inventory_df = self._build_inventory_dataframe(categories, areas)
        print(f"✅ Inventory loaded: {len(inventory_df)} units across {len(set(inventory_df['Category']))} categories")
        
        # Show cache statistics
        cache_stats = self.get_cache_stats()
        print(f"💾 Cache stats: {cache_stats['categories_cache_size']} categories, {cache_stats['areas_cache_size']} areas cached")
        
        return inventory_df
    
    def fetch_reservations_data(self, property_id: int, property_name: str) -> pd.DataFrame:
        """Fetch live reservations data from RMS API for specified property with caching"""
        print(f"\n📋 FETCHING RESERVATIONS DATA")
        print("=" * 40)
        print(f"🎯 Target Period: {self.constraint_start_date} to {self.constraint_end_date}")
        
        # Get categories for filtering (with caching)
        categories = self._get_categories(property_id, property_name)
        if not categories:
            print("❌ No categories found for reservation filtering")
            return pd.DataFrame()
        
        category_ids = [cat['id'] for cat in categories]
        print(f"🔗 Using {len(category_ids)} category IDs for filtering")
        
        # Build reservation search payload
        search_payload = {
            "propertyIds": [property_id],
            "categoryIds": category_ids,
            "arriveFrom": "2000-01-01 00:00:00",
            "arriveTo": f"{self.constraint_end_date} 23:59:59",
            "departFrom": f"{self.constraint_start_date} 00:00:00",
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
        
        try:
            print(f"📡 Searching reservations...")
            response = self.session.post(
                f"{self.base_url}/reservations/search", 
                json=search_payload,
                params=params
            )
            
            if response.status_code == 200:
                reservations_data = response.json()
                print(f"✅ Found {len(reservations_data)} reservations")
                
                # Record endpoint data for monitoring
                self._record_endpoint_data(property_id, property_name, 'reservations', len(reservations_data), 2000)
                
                # Build reservations DataFrame
                reservations_df = self._build_reservations_dataframe(reservations_data, categories, property_id)
                return reservations_df
            else:
                print(f"❌ Reservations search failed: Status {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Reservations search error: {e}")
            return pd.DataFrame()

    def _get_categories(self, property_id: int, property_name: str = None) -> List[Dict]:
        """Get filtered categories from RMS API for specified property with caching"""
        
        # Check cache first
        if property_id in self._categories_cache and self._is_cache_valid(property_id):
            cached_categories = self._categories_cache[property_id]
            print(f"   📊 Using cached categories: {len(cached_categories)} active categories")
            return cached_categories
        
        # Fetch from API if not cached or cache expired
        params = {
            'propertyId': property_id,
            'modelType': 'Full',
            'limit': 2000
        }
        
        try:
            response = self.session.get(f"{self.base_url}/categories", params=params)
            
            if response.status_code == 200:
                all_categories = response.json()
                
                # Filter: inactive=false AND availableToIbe=true
                filtered_categories = [
                    cat for cat in all_categories 
                    if not cat.get('inactive', False) and cat.get('availableToIbe', False)
                ]
                
                # Cache the results
                self._categories_cache[property_id] = filtered_categories
                self._update_cache_timestamp(property_id)
                
                # Record endpoint data for monitoring (only if property_name provided)
                if property_name:
                    self._record_endpoint_data(property_id, property_name, 'categories', len(all_categories), 2000)
                
                print(f"   📊 Fetched {len(all_categories)} total, {len(filtered_categories)} active categories (cached)")
                return filtered_categories
            else:
                print(f"   ❌ Categories API failed: Status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ❌ Categories error: {e}")
            return []
    
    def _get_areas(self, property_id: int, property_name: str = None) -> List[Dict]:
        """Get filtered areas/units from RMS API for specified property with caching"""
        
        # Check cache first
        if property_id in self._areas_cache and self._is_cache_valid(property_id):
            cached_areas = self._areas_cache[property_id]
            print(f"   🏠 Using cached areas: {len(cached_areas)} active areas")
            return cached_areas
        
        # Fetch from API if not cached or cache expired
        params = {
            'propertyId': property_id,
            'modelType': 'Full',
            'limit': 2000
        }
        
        try:
            response = self.session.get(f"{self.base_url}/areas", params=params)
            
            if response.status_code == 200:
                all_areas = response.json()
                
                # Filter: inactive=false AND statisticsStatus=true
                filtered_areas = [
                    area for area in all_areas 
                    if not area.get('inactive', False) and area.get('statisticsStatus', True)
                ]
                
                # Cache the results
                self._areas_cache[property_id] = filtered_areas
                self._update_cache_timestamp(property_id)
                
                # Record endpoint data for monitoring (only if property_name provided)
                if property_name:
                    self._record_endpoint_data(property_id, property_name, 'areas', len(all_areas), 2000)
                
                print(f"   🏠 Fetched {len(all_areas)} total, {len(filtered_areas)} active areas (cached)")
                return filtered_areas
            else:
                print(f"   ❌ Areas API failed: Status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ❌ Areas error: {e}")
            return []
    
    def _build_inventory_dataframe(self, categories: List[Dict], areas: List[Dict]) -> pd.DataFrame:
        """Build inventory DataFrame matching original format"""
        
        # Create category lookup
        category_lookup = {cat['id']: cat['name'] for cat in categories}
        valid_category_ids = set(category_lookup.keys())
        
        inventory_data = []
        
        for area in areas:
            category_id = area.get('categoryId')
            area_name = area.get('name', f"Area-{area.get('id', 'Unknown')}")
            
            # Only include areas with valid categories
            if category_id and category_id in valid_category_ids:
                category_name = category_lookup[category_id]
                inventory_data.append({
                    'Category': category_name,
                    'Unit/Site': area_name
                })
        
        return pd.DataFrame(inventory_data)

    def _build_reservations_dataframe(self, reservations_data: List[Dict], categories: List[Dict], property_id: int) -> pd.DataFrame:
        """Build reservations DataFrame with correct format"""
        
        # Get area lookup for area names (filtered areas only)
        areas = self._get_areas(property_id)
        area_lookup = {area['id']: area['name'] for area in areas}
        
        # Create category lookup
        category_lookup = {cat['id']: cat['name'] for cat in categories}
        
        reservation_data = []
        filtered_out_count = 0
        
        for res in reservations_data:
            try:
                # Extract key fields
                res_id = res.get('id', '')
                guest_surname = res.get('guestSurname', '')
                area_id = res.get('areaId')
                category_id = res.get('categoryId') 
                
                # Filter out reservations for excluded areas
                if area_id not in area_lookup:
                    filtered_out_count += 1
                    continue
                
                area_name = area_lookup[area_id]
                category_name = category_lookup.get(category_id, 'Unknown Category')
                
                # Parse dates
                arrival_date = res.get('arrivalDate', '')
                departure_date = res.get('departureDate', '')
                
                # Format dates
                arrive_formatted = self._format_date_for_analysis(arrival_date)
                depart_formatted = self._format_date_for_analysis(departure_date)
                
                # Calculate nights
                nights = self._calculate_nights(arrival_date, departure_date)
                
                # Map status
                status = self._map_reservation_status(res.get('status', ''))
                
                # Check if reservation is fixed
                is_fixed = res.get('fixedRes', False)
                
                reservation_data.append({
                    'Category': category_name,
                    'Res No': str(res_id),
                    'Surname': guest_surname,
                    'Unit/Site': area_name,
                    'Arrive': arrive_formatted,
                    'Depart': depart_formatted,
                    'Nights': str(nights),
                    'Status': status,
                    'Fixed': str(is_fixed)
                })
                
            except Exception as e:
                print(f"   ⚠️  Error processing reservation {res.get('id', 'unknown')}: {e}")
                continue
        
        df = pd.DataFrame(reservation_data)
        print(f"✅ Built {len(df)} reservation records")
        
        # Log filtering results
        if filtered_out_count > 0:
            print(f"🚫 Filtered out {filtered_out_count} reservations for excluded areas")
        
        # Count fixed reservations
        fixed_count = sum(1 for _, row in df.iterrows() if self._is_reservation_fixed(row))
        if fixed_count > 0:
            print(f"🔒 Found {fixed_count} fixed reservations (cannot be moved)")
        
        return df
    
    def _format_date_for_analysis(self, api_date: str) -> str:
        """Format API date for analysis (d/m/yyyy H:MM format)"""
        if not api_date:
            return ''
        
        try:
            if 'T' in api_date:
                dt = datetime.fromisoformat(api_date.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(api_date, '%Y-%m-%d %H:%M:%S')
            
            return dt.strftime('%d/%m/%Y %H:%M')
            
        except Exception as e:
            print(f"   ⚠️  Date format error for '{api_date}': {e}")
            return api_date
    
    def _calculate_nights(self, arrival_date: str, departure_date: str) -> int:
        """Calculate number of nights between arrival and departure"""
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
            print(f"   ⚠️  Night calculation error: {e}")
            return 0
    
    def _map_reservation_status(self, api_status: str) -> str:
        """Map RMS API status to expected values"""
        if not api_status:
            return 'Unknown'
        
        status_mapping = {
            'confirmed': 'Confirmed',
            'unconfirmed': 'Unconfirmed', 
            'arrived': 'Arrived',
            'departed': 'Departed',
            'cancelled': 'Cancelled',
            'maintenance': 'Maintenance',
            'quote': 'Quote',
            'stopsell': 'StopSell',
            'owneroccupied': 'OwnerOccupied',
            'pencil': 'Pencil'
        }
        
        return status_mapping.get(api_status.lower(), api_status)

    def _is_reservation_fixed(self, reservation_row) -> bool:
        """Check if reservation is marked as fixed"""
        if 'Fixed' in reservation_row:
            fixed_value = reservation_row['Fixed']
            if isinstance(fixed_value, bool):
                return fixed_value
            elif isinstance(fixed_value, str):
                return fixed_value.lower() in ['true', '1', 'yes']
        return False
    
    def extract_state_code(self, property_data: Dict) -> Optional[str]:
        """
        Extract state code from property data
        
        Args:
            property_data: Property data dictionary from RMS API
            
        Returns:
            State code (VIC, NSW, QLD, etc.) or None if not found
        """
        # Try multiple possible field names
        state_fields = ['state', 'stateCode', 'region', 'location', 'address']
        
        for field in state_fields:
            if field in property_data and property_data[field]:
                state_code = str(property_data[field]).upper()
                if state_code in self.STATE_COUNTRY_MAPPING:
                    self.logger.debug(f"Found state code '{state_code}' in field '{field}'")
                    return state_code
        
        # Fallback: extract from property name or code
        property_name = property_data.get('name', '').upper()
        property_code = property_data.get('code', '').upper()
        
        # Look for state abbreviations in name/code
        for state_code in self.STATE_COUNTRY_MAPPING.keys():
            if state_code in property_name or state_code in property_code:
                self.logger.debug(f"Found state code '{state_code}' in property name/code")
                return state_code
        
        self.logger.warning(f"Could not extract state code from property: {property_data.get('name', 'Unknown')}")
        return None
    
    def get_property_with_state(self, property_id: int) -> Optional[Dict]:
        """
        Get property data with extracted state code
        
        Args:
            property_id: Property ID to fetch
            
        Returns:
            Property data with state_code field added, or None if not found
        """
        # Find property in all_properties
        for property_data in self.all_properties:
            if property_data.get('id') == property_id:
                # Extract state code
                state_code = self.extract_state_code(property_data)
                property_data['state_code'] = state_code
                return property_data
        
        self.logger.warning(f"Property {property_id} not found in all_properties")
        return None
    
    def get_holiday_aware_date_range(self, property_state: str, holiday_client=None) -> Tuple[date, date]:
        """
        Calculate holiday-aware date range for a property
        
        Args:
            property_state: State code for the property
            holiday_client: Optional HolidayClient instance
            
        Returns:
            Tuple of (start_date, end_date) for holiday-aware analysis
        """
        if not holiday_client:
            self.logger.debug(f"No holiday client provided, using base date range for {property_state}")
            return self.constraint_start_date, self.constraint_end_date
        
        try:
            # Calculate holiday-aware date range
            start_date, end_date = holiday_client.get_holiday_aware_date_range(
                property_state, 
                self.constraint_start_date, 
                self.constraint_end_date
            )
            
            self.logger.info(f"Holiday-aware date range for {property_state}: {start_date} to {end_date}")
            return start_date, end_date
            
        except Exception as e:
            self.logger.error(f"Error calculating holiday-aware date range for {property_state}: {e}")
            # Fallback to base date range
            return self.constraint_start_date, self.constraint_end_date