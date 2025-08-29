"""
RMS Reservation Update Service
Handles updating reservations in RMS API for move operations
"""

import requests
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from app.core.config import settings
from app.services.lightweight_rms_client import LightweightRMSClient

logger = logging.getLogger(__name__)

class RMSReservationService:
    """Service for updating reservations in RMS API"""
    
    def __init__(self):
        self.base_url = "https://restapi12.rmscloud.com"
        self.session = requests.Session()
        self.token = None
        self.token_expiry = None
        
    def authenticate(self) -> bool:
        """Authenticate with RMS API using stored credentials"""
        try:
            auth_payload = {
                "AgentId": settings.AGENT_ID,
                "AgentPassword": settings.AGENT_PASSWORD,
                "ClientId": settings.CLIENT_ID,
                "ClientPassword": settings.CLIENT_PASSWORD,
                "UseTrainingDatabase": settings.USE_TRAINING_DB,
                "ModuleType": ["distribution"]
            }
            
            logger.info("Authenticating with RMS API for reservation updates")
            response = self.session.post(f"{self.base_url}/authToken", json=auth_payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                if self.token:
                    # Set authentication header for subsequent requests
                    self.session.headers.update({'authtoken': self.token})
                    logger.info("✅ RMS authentication successful for reservation updates")
                    return True
                else:
                    logger.error("No token received from RMS API")
                    return False
            else:
                logger.error(f"RMS authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error during RMS authentication: {e}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token"""
        if not self.token:
            logger.info("No token available, authenticating...")
            return self.authenticate()
        
        # For now, assume token is valid. In production, we might want to check expiry
        return True
    
    async def update_reservation_area(self, reservation_id: str, target_area_id: int, username: str, 
                                    current_unit_name: str = None, target_unit_name: str = None) -> Dict[str, Any]:
        """
        Update a reservation's area assignment in RMS
        
        Args:
            reservation_id: RMS reservation ID
            target_area_id: Target area/unit ID to move to
            username: Username of the person authorizing the move
            current_unit_name: Current unit name (for logging)
            target_unit_name: Target unit name (for logging)
            
        Returns:
            Dict with success status, message, and any error details
        """
        if not self._ensure_authenticated():
            return {
                "success": False,
                "error": "RMS authentication failed",
                "error_type": "authentication"
            }
        
        try:
            # Prepare the PATCH payload - only include fields we want to update
            update_payload = {
                "areaId": target_area_id,
                "notes": f"Moved via RMS Defragmentation System - Authorized by {username}"
            }
            
            # Set required query parameters
            params = {
                'ignoreMandatoryFieldWarnings': 'true',
                'preventRateRecalculation': 'true'
            }
            
            # Log the operation for audit trail
            logger.info(f"Updating reservation {reservation_id}: {current_unit_name} → {target_unit_name} (area ID: {target_area_id})")
            logger.info(f"Update payload: {update_payload}")
            logger.info(f"Update params: {params}")
            
            # Make the API call
            # Use PATCH method to update only specific fields
            url = f"{self.base_url}/reservations/{reservation_id}"
            response = self.session.patch(url, json=update_payload, params=params, timeout=30)
            
            logger.info(f"RMS API response: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully updated reservation {reservation_id} to area {target_area_id}")
                return {
                    "success": True,
                    "message": f"Reservation moved from {current_unit_name} to {target_unit_name}",
                    "reservation_id": reservation_id,
                    "target_area_id": target_area_id
                }
            else:
                # Parse error response
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', f'HTTP {response.status_code}')
                    error_details = error_data.get('details', 'No additional details')
                except:
                    error_message = f"HTTP {response.status_code}: {response.text}"
                    error_details = response.text
                
                logger.error(f"❌ Failed to update reservation {reservation_id}: {error_message}")
                logger.error(f"Error details: {error_details}")
                
                # Categorize error types for better handling
                error_type = "unknown"
                if response.status_code == 400:
                    if "area" in error_message.lower() or "unavailable" in error_message.lower():
                        error_type = "area_unavailable"
                    else:
                        error_type = "validation_error"
                elif response.status_code == 401:
                    error_type = "authentication"
                elif response.status_code == 403:
                    error_type = "permission"
                elif response.status_code == 404:
                    error_type = "not_found"
                elif response.status_code >= 500:
                    error_type = "server_error"
                
                return {
                    "success": False,
                    "error": error_message,
                    "error_details": error_details,
                    "error_type": error_type,
                    "http_status": response.status_code,
                    "reservation_id": reservation_id,
                    "target_area_id": target_area_id
                }
                
        except requests.Timeout:
            error_msg = f"Timeout while updating reservation {reservation_id}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "timeout",
                "reservation_id": reservation_id
            }
        except requests.ConnectionError as e:
            error_msg = f"Connection error while updating reservation {reservation_id}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "connection",
                "reservation_id": reservation_id
            }
        except Exception as e:
            error_msg = f"Unexpected error updating reservation {reservation_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "unexpected",
                "reservation_id": reservation_id
            }
    
    async def update_multiple_reservations(self, move_suggestions: List[Dict[str, Any]], username: str) -> Dict[str, Any]:
        """
        Update multiple reservations sequentially
        
        Args:
            move_suggestions: List of move suggestion dictionaries
            username: Username of the person authorizing the moves
            
        Returns:
            Dict with overall results, success count, failure count, and detailed results
        """
        logger.info(f"Starting batch update of {len(move_suggestions)} reservations")
        
        results = {
            "total_moves": len(move_suggestions),
            "successful_moves": 0,
            "failed_moves": 0,
            "detailed_results": [],
            "success": False,
            "message": ""
        }
        
        for i, move in enumerate(move_suggestions):
            logger.info(f"Processing move {i+1}/{len(move_suggestions)}")
            
            # Extract required data from move suggestion
            reservation_id = move.get('reservation_id')
            target_area_id = move.get('to_area_id')
            current_unit = move.get('from_unit', 'Unknown')
            target_unit = move.get('to_unit', 'Unknown')
            move_id = move.get('move_id')  # Extract move_id for frontend UI updates
            
            # Send real-time progress update via WebSocket BEFORE processing
            try:
                from app.core.websocket_manager import websocket_manager
                progress_percentage = (i / len(move_suggestions)) * 100  # Progress at start of move
                await websocket_manager.send_progress_update(
                    property_code="MOVES", 
                    step="apply_move",
                    message=f"Starting move {i + 1}/{len(move_suggestions)}: {current_unit} → {target_unit}",
                    progress=progress_percentage
                )
            except Exception as e:
                logger.warning(f"Failed to send WebSocket progress update: {e}")
            
            # Validate required fields
            if not reservation_id:
                logger.error(f"Move {i+1}: Missing reservation_id")
                results["detailed_results"].append({
                    "move_index": i,
                    "success": False,
                    "error": "Missing reservation_id",
                    "current_unit": current_unit,
                    "target_unit": target_unit
                })
                results["failed_moves"] += 1
                continue
                
            if not target_area_id:
                logger.error(f"Move {i+1}: Missing target area ID")
                results["detailed_results"].append({
                    "move_index": i,
                    "reservation_id": reservation_id,
                    "success": False,
                    "error": "Missing target area ID - area mapping failed",
                    "current_unit": current_unit,
                    "target_unit": target_unit
                })
                results["failed_moves"] += 1
                continue
            
            # Attempt the update
            update_result = await self.update_reservation_area(
                reservation_id=reservation_id,
                target_area_id=target_area_id,
                username=username,
                current_unit_name=current_unit,
                target_unit_name=target_unit
            )
            
            # Record the result
            detailed_result = {
                "move_index": i,
                "move_id": reservation_id,  # Use reservation_id as move_id for UI updates
                "reservation_id": reservation_id,
                "current_unit": current_unit,
                "target_unit": target_unit,
                "target_area_id": target_area_id,
                **update_result
            }
            
            results["detailed_results"].append(detailed_result)
            
            if update_result["success"]:
                results["successful_moves"] += 1
                logger.info(f"✅ Move {i+1}/{len(move_suggestions)}: Success")
            else:
                results["failed_moves"] += 1
                logger.error(f"❌ Move {i+1}/{len(move_suggestions)}: Failed - {update_result.get('error', 'Unknown error')}")
            
            # Send progress update AFTER processing each move
            try:
                progress_percentage = ((i + 1) / len(move_suggestions)) * 100  # Progress after completing move
                status = "✅ Completed" if update_result["success"] else "❌ Failed"
                await websocket_manager.send_progress_update(
                    property_code="MOVES", 
                    step="apply_move",
                    message=f"{status} move {i + 1}/{len(move_suggestions)}: {current_unit} → {target_unit}",
                    progress=progress_percentage
                )
            except Exception as e:
                logger.warning(f"Failed to send WebSocket completion update: {e}")
        
        # Set overall success and message
        if results["successful_moves"] == results["total_moves"]:
            results["success"] = True
            results["message"] = f"All {results['successful_moves']} moves completed successfully"
        elif results["successful_moves"] > 0:
            results["success"] = True  # Partial success
            results["message"] = f"{results['successful_moves']} of {results['total_moves']} moves completed successfully"
        else:
            results["success"] = False
            results["message"] = f"All {results['failed_moves']} moves failed"
        
        logger.info(f"Batch update completed: {results['successful_moves']}/{results['total_moves']} successful")
        return results
