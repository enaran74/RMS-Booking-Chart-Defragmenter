"""
Defragmentation service for generating move suggestions
Uses lightweight RMS API integration for live booking data analysis
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.models.defrag_move import DefragMove
from app.models.move_batch import MoveBatch
from app.models.property import Property
from app.core.websocket_manager import websocket_manager
from app.core.config import settings
from app.services.lightweight_rms_client import LightweightRMSClient

logger = logging.getLogger(__name__)

class DefragService:
    """Simplified service for managing defragmentation move suggestions using real RMS API"""
    
    def __init__(self):
        logger.info("Initializing DefragService with lightweight RMS integration")
        self.rms_client = LightweightRMSClient()
    
    def _get_rms_property_id(self, property_obj) -> int:
        """Get RMS property ID from database property object"""
        if hasattr(property_obj, 'rms_property_id') and property_obj.rms_property_id:
            logger.info(f"🔧 Using stored RMS Property ID: {property_obj.property_code} -> {property_obj.rms_property_id}")
            return property_obj.rms_property_id
        else:
            # Fallback to hardcoded mapping for properties that haven't been refreshed yet
            logger.warning(f"⚠️ No RMS property ID stored for {property_obj.property_code}, using fallback mapping")
            rms_id_mapping = {
                'CKAT': 128,  # Katherine - was incorrectly mapped to 81
                'WCOO': 81,   # Coogee Beach - correctly mapped
            }
            
            clean_code = property_obj.property_code.rstrip('-').upper()
            if clean_code in rms_id_mapping:
                logger.info(f"🔧 Using fallback RMS Property ID mapping: {clean_code} -> {rms_id_mapping[clean_code]}")
                return rms_id_mapping[clean_code]
            else:
                logger.error(f"❌ No RMS property ID available for {property_obj.property_code}. Please refresh properties in Setup page.")
                return None
    
    async def get_move_suggestions(self, property_code: str, force_refresh: bool = False, db: Session = None) -> Dict[str, Any]:
        """Generate fresh move suggestions from RMS API and store them permanently"""
        print(f"⭐⭐⭐ GET_MOVE_SUGGESTIONS CALLED FOR {property_code} ⭐⭐⭐")
        logger.info(f"⭐ GET_MOVE_SUGGESTIONS CALLED FOR {property_code}")
        logger.info(f"Generating move suggestions for {property_code}")
        
        # Send initial progress update
        await websocket_manager.send_progress_update(
            property_code, 
            "start", 
            f"Starting move suggestions generation for {property_code}",
            progress=0.0
        )
        
        try:
            # Get the property object first
            from app.models.property import Property
            property_obj = db.query(Property).filter(Property.property_code == property_code.upper()).first()
            if not property_obj:
                raise Exception(f"Property {property_code.upper()} not found in database")
            
            # Always generate fresh suggestions from RMS API
            await websocket_manager.send_progress_update(
                property_code, 
                "rms_connect", 
                "Connecting to RMS API...",
                progress=20.0
            )
            
            # Get the correct RMS property ID from the database property object
            rms_property_id = self._get_rms_property_id(property_obj)
            if rms_property_id is None:
                raise Exception(f"Unable to determine correct RMS property ID for {property_code}. Please refresh properties in Setup page.")
            
            # Generate move suggestions using lightweight RMS API with correct property ID
            suggestions = await self._generate_lightweight_rms_suggestions(property_code, property_obj, rms_property_id)
            
            await websocket_manager.send_progress_update(
                property_code, 
                "rms_analysis", 
                f"Analyzing suggestions for {property_code}...",
                progress=70.0
            )
            
            # Store the suggestions in the database
            move_count = len(suggestions)
            
            # Create MoveBatch first
            from app.models.move_batch import MoveBatch
            
            batch = MoveBatch(
                property_code=property_code.upper(),
                total_moves=move_count,
                status='completed'
            )
            db.add(batch)
            db.commit()
            db.refresh(batch)
            
            # Create DefragMove record with explicit boolean flags
            defrag_move = DefragMove(
                property_id=property_obj.id,
                property_code=property_code.upper(),
                analysis_date=datetime.now(),
                move_count=move_count,
                move_data={"moves": suggestions, "analysis_date": datetime.now().isoformat()},
                status='pending',
                batch_id=batch.id,
                is_processed=False,
                is_rejected=False
            )
            
            db.add(defrag_move)
            db.commit()
            db.refresh(defrag_move)
            
            await websocket_manager.send_progress_update(
                property_code, 
                "storage", 
                f"Stored {move_count} move suggestions",
                progress=100.0
            )
            
            logger.info(f"Successfully generated and stored {move_count} suggestions for {property_code}")
            
            return {
                "move_count": move_count,
                "is_cached": False,
                "cache_age_hours": 0,
                "property_code": property_code.upper(),
                "analysis_date": defrag_move.analysis_date.isoformat(),
                "moves": suggestions,
                "batch_info": None
            }
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions for {property_code}: {str(e)}")
            await websocket_manager.send_error(
                property_code,
                f"Failed to generate suggestions: {str(e)}",
                "generation_failed"
            )
            raise e
    
    async def _generate_lightweight_rms_suggestions(self, property_code: str, property_obj, rms_property_id: int) -> List[Dict[str, Any]]:
        """Generate move suggestions using lightweight RMS API integration"""
        print(f"🔥🔥🔥 _GENERATE_LIGHTWEIGHT_RMS_SUGGESTIONS CALLED FOR {property_code} 🔥🔥🔥")
        logger.info(f"🔥 _GENERATE_LIGHTWEIGHT_RMS_SUGGESTIONS CALLED FOR {property_code}")
        logger.info(f"Generating lightweight RMS suggestions for {property_code}")
        
        try:
            # Step 1: Authenticate with RMS API
            await websocket_manager.send_progress_update(
                property_code, 
                "rms_auth", 
                "Authenticating with RMS API...",
                progress=25.0
            )
            
            logger.info(f"Authenticating with RMS API for {property_code}")
            auth_success = self.rms_client.authenticate()
            if not auth_success:
                error_msg = f"RMS authentication failed for {property_code}. Check your RMS credentials in config.env"
                logger.error(error_msg)
                await websocket_manager.send_progress_update(
                    property_code,
                    "rms_auth_failed",
                    error_msg,
                    progress=25.0
                )
                raise Exception(error_msg)
            
            # Step 2: Perform simple analysis using lightweight client
            await websocket_manager.send_progress_update(
                property_code, 
                "rms_analysis", 
                "Analyzing booking data for optimization opportunities...",
                progress=60.0
            )
            
            logger.info(f"Running simple defragmentation analysis for RMS property ID {rms_property_id} (was using incorrect DB ID {property_obj.id})")

            # Send debug info about starting RMS API calls
            await websocket_manager.send_progress_update(
                property_code,
                "rms_api_start",
                f"🔍 Starting RMS API calls for RMS property {rms_property_id}",
                progress=65.0
            )

            # Use the lightweight client's analysis method with CORRECT RMS property ID
            raw_suggestions = await self.rms_client.analyze_simple_defragmentation(rms_property_id, property_code)

            # Send debug info about RMS API results
            await websocket_manager.send_progress_update(
                property_code,
                "rms_api_complete",
                f"📊 RMS API calls completed: {len(raw_suggestions)} suggestions generated",
                progress=85.0
            )
            
            # Step 3: Fetch area mappings for move operations
            await websocket_manager.send_progress_update(
                property_code,
                "area_mapping",
                "📍 Fetching area mappings for move operations...",
                progress=87.0
            )
            
            areas = self.rms_client.get_property_areas_for_moves(rms_property_id)
            area_name_to_id = self.rms_client.create_area_name_to_id_mapping(areas) if areas else {}
            
            logger.info(f"Created area mapping with {len(area_name_to_id)} area name-to-ID mappings")
            await websocket_manager.send_progress_update(
                property_code,
                "area_mapping_complete",
                f"✅ Area mapping completed: {len(area_name_to_id)} areas mapped",
                progress=90.0
            )
            
            # Convert suggestions to proper JSON format with area IDs
            logger.info(f"Converting {len(raw_suggestions)} raw suggestions to JSON format with area IDs")
            suggestions = self._convert_suggestions_to_json(raw_suggestions, property_code, area_name_to_id)
            logger.info(f"Converted to {len(suggestions)} formatted suggestions with area ID mappings")
            
            if not suggestions:
                error_msg = f"No move suggestions generated by RMS API for {property_code}. Property may have no reservations or optimization opportunities."
                logger.warning(error_msg)
                await websocket_manager.send_progress_update(
                    property_code,
                    "no_suggestions",
                    error_msg,
                    progress=80.0
                )
                # Return empty list instead of sample data
                return []
            
            logger.info(f"Generated {len(suggestions)} lightweight RMS suggestions for {property_code}")
            return suggestions
            
        except Exception as e:
            error_msg = f"Failed to generate lightweight RMS suggestions for {property_code}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await websocket_manager.send_progress_update(
                property_code,
                "rms_error",
                error_msg,
                progress=60.0
            )
            # Re-raise the exception instead of falling back to sample data
            raise Exception(error_msg)
    
    def _convert_suggestions_to_json(self, raw_suggestions: List[Dict], property_code: str, area_name_to_id: Dict[str, int] = None) -> List[Dict[str, Any]]:
        """Convert raw defragmentation suggestions to our JSON format with area ID mapping"""
        logger.info(f"Converting {len(raw_suggestions)} raw suggestions for {property_code}")
        
        if area_name_to_id is None:
            area_name_to_id = {}
            logger.warning("No area name-to-ID mapping provided - move operations will not be possible")
        
        converted_suggestions = []
        mapping_errors = 0
        
        for idx, suggestion in enumerate(raw_suggestions):
            try:
                # Extract unit names
                from_unit = suggestion.get("current_unit", "N/A")
                to_unit = suggestion.get("target_unit", "N/A")
                
                # Map unit names to area IDs
                from_area_id = area_name_to_id.get(from_unit)
                to_area_id = area_name_to_id.get(to_unit)
                
                # Enhanced mapping debugging
                logger.info(f"🔍 Mapping attempt for suggestion {idx}:")
                logger.info(f"   From unit: '{from_unit}' → Area ID: {from_area_id}")
                logger.info(f"   To unit: '{to_unit}' → Area ID: {to_area_id}")
                
                # Log mapping issues for debugging
                if from_unit != "N/A" and from_area_id is None:
                    logger.warning(f"❌ Could not map 'from_unit' '{from_unit}' to area ID")
                    logger.warning(f"   Available area names: {list(area_name_to_id.keys())[:10]}...")
                    mapping_errors += 1
                if to_unit != "N/A" and to_area_id is None:
                    logger.warning(f"❌ Could not map 'to_unit' '{to_unit}' to area ID")
                    logger.warning(f"   Searching for exact match in {len(area_name_to_id)} available areas")
                    # Check for partial matches
                    partial_matches = [name for name in area_name_to_id.keys() if to_unit.lower() in name.lower() or name.lower() in to_unit.lower()]
                    if partial_matches:
                        logger.warning(f"   🔍 Potential partial matches: {partial_matches[:5]}")
                    mapping_errors += 1
                
                # Extract key fields from the suggestion
                converted_suggestion = {
                    "from_unit": from_unit,
                    "to_unit": to_unit,
                    # NEW: Add area IDs for RMS API updates
                    "from_area_id": from_area_id,
                    "to_area_id": to_area_id,
                    "guest": suggestion.get("guest_name", "N/A"),
                    "check_in": suggestion.get("check_in", "N/A"),
                    "check_out": suggestion.get("check_out", "N/A"),
                    "strategic_importance": self._map_strategic_importance(suggestion.get("strategic_importance", 0.0)),
                    "score": int(suggestion.get("score", 0)),
                    "reason": suggestion.get("reason", "Optimization opportunity identified"),
                    # Additional metadata
                    "reservation_id": suggestion.get("reservation_id", None),
                    "category": suggestion.get("category", "N/A"),
                    "nights_freed": suggestion.get("nights_freed", 0),
                    "analysis_date": datetime.now().isoformat()
                }
                
                converted_suggestions.append(converted_suggestion)
                
            except Exception as e:
                logger.warning(f"Failed to convert suggestion {idx} for {property_code}: {e}")
                continue
        
        logger.info(f"Successfully converted {len(converted_suggestions)} suggestions for {property_code}")
        
        # Log area mapping results
        if mapping_errors > 0:
            logger.warning(f"Area mapping issues: {mapping_errors} unit names could not be mapped to area IDs")
        else:
            logger.info(f"✅ All unit names successfully mapped to area IDs")
        
        # Check for potential duplicates
        reservations_seen = {}
        duplicates_found = 0
        for suggestion in converted_suggestions:
            res_id = suggestion.get("reservation_id")
            if res_id and res_id != "N/A":
                if res_id in reservations_seen:
                    duplicates_found += 1
                    logger.warning(f"Potential duplicate found for reservation {res_id}: {suggestion.get('guest', 'Unknown')} from {suggestion.get('from_unit', 'Unknown')} to {suggestion.get('to_unit', 'Unknown')}")
                else:
                    reservations_seen[res_id] = suggestion
        
        if duplicates_found > 0:
            logger.warning(f"Found {duplicates_found} potential duplicate suggestions for {property_code}")
        
        # CRITICAL FIX: Filter to keep only the BEST suggestion per reservation (like original defrag logic)
        if duplicates_found > 0:
            logger.info(f"Filtering {len(converted_suggestions)} suggestions to keep only best move per reservation")
            
            # Group suggestions by reservation ID
            suggestions_by_reservation = {}
            for suggestion in converted_suggestions:
                res_id = suggestion.get("reservation_id")
                if res_id and res_id != "N/A":
                    if res_id not in suggestions_by_reservation:
                        suggestions_by_reservation[res_id] = []
                    suggestions_by_reservation[res_id].append(suggestion)
            
            # Keep only the highest scoring suggestion per reservation
            filtered_suggestions = []
            for res_id, reservation_suggestions in suggestions_by_reservation.items():
                if len(reservation_suggestions) == 1:
                    # Only one suggestion, keep it
                    filtered_suggestions.append(reservation_suggestions[0])
                else:
                    # Multiple suggestions, keep the highest scoring one
                    best_suggestion = max(reservation_suggestions, key=lambda s: s.get("score", 0))
                    filtered_suggestions.append(best_suggestion)
                    logger.info(f"Filtered reservation {res_id}: kept best scoring suggestion (score: {best_suggestion.get('score', 0)})")
            
            # Add any suggestions without reservation IDs
            for suggestion in converted_suggestions:
                res_id = suggestion.get("reservation_id")
                if not res_id or res_id == "N/A":
                    filtered_suggestions.append(suggestion)
            
            logger.info(f"Filtered from {len(converted_suggestions)} to {len(filtered_suggestions)} suggestions (1 per reservation)")
            return filtered_suggestions
        
        return converted_suggestions
    
    async def _generate_sample_suggestions(self, property_code: str) -> List[Dict[str, Any]]:
        """Generate sample move suggestions for testing"""
        logger.info(f"Generating sample suggestions for {property_code}")
        
        # This is a placeholder - replace with actual defragmentation logic
        sample_suggestions = [
            {
                "from_unit": "A101",
                "to_unit": "B205",
                "guest": "John Smith",
                "check_in": "2024-01-15",
                "check_out": "2024-01-20",
                "strategic_importance": "High",
                "score": 85,
                "reason": "Better unit utilization and guest satisfaction"
            },
            {
                "from_unit": "C301",
                "to_unit": "A102",
                "guest": "Sarah Johnson",
                "check_in": "2024-01-16",
                "check_out": "2024-01-22",
                "strategic_importance": "Medium",
                "score": 72,
                "reason": "Improved revenue optimization"
            },
            {
                "from_unit": "B104",
                "to_unit": "D401",
                "guest": "Mike Wilson",
                "check_in": "2024-01-17",
                "check_out": "2024-01-19",
                "strategic_importance": "Low",
                "score": 65,
                "reason": "Better unit availability for future bookings"
            }
        ]
        
        return sample_suggestions
    
    def _map_strategic_importance(self, importance_value) -> str:
        """Map strategic importance to string category (handles both numeric and string inputs)"""
        # If it's already a string, return it directly
        if isinstance(importance_value, str):
            return importance_value
        
        # If it's numeric, convert to string category
        try:
            importance_float = float(importance_value)
            if importance_float >= 0.7:
                return "High"
            elif importance_float >= 0.4:
                return "Medium"
            else:
                return "Low"
        except (ValueError, TypeError):
            return "Low"  # Default fallback
