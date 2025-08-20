"""
Defragmentation service for managing move suggestions and cache
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.models.defrag_move import DefragMove
from app.models.move_batch import MoveBatch
from app.models.property import Property
from app.services.rms_service import RMSService
from app.core.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class DefragService:
    """Service for managing defragmentation move suggestions"""
    
    def __init__(self):
        self.rms_service = RMSService()
    
    async def get_move_suggestions(self, property_code: str, force_refresh: bool = False, db: Session = None) -> Dict[str, Any]:
        """Generate fresh move suggestions from RMS API and store them permanently"""
        logger.info(f"Getting move suggestions for {property_code} (force_refresh: {force_refresh})")
        
        # Send initial progress update
        await websocket_manager.send_progress_update(
            property_code, 
            "start", 
            f"Starting move suggestions retrieval for {property_code}",
            progress=0.0
        )
        
        try:
            # Check cache status first
            cache_status = await self._check_cache_status(property_code, db)
            
            await websocket_manager.send_progress_update(
                property_code, 
                "cache_check", 
                f"Cache status: {'Fresh' if cache_status['is_fresh'] else 'Stale'} (age: {cache_status['age_hours']:.1f}h)" if cache_status['age_hours'] is not None else f"Cache status: {'Fresh' if cache_status['is_fresh'] else 'Stale'} (no age data)",
                progress=10.0,
                data=cache_status
            )
            
            # If cache is fresh and not forcing refresh, return cached data
            if cache_status['has_cache'] and cache_status['is_fresh'] and not force_refresh:
                await websocket_manager.send_progress_update(
                    property_code, 
                    "cache_hit", 
                    f"Using cached data: {cache_status['move_count']} moves available",
                    progress=100.0
                )
                
                cached_moves = await self._get_cached_suggestions(property_code, db)
                return {
                    "move_count": cache_status['move_count'],
                    "is_cached": True,
                    "cache_age_hours": cache_status['age_hours'],
                    "analysis_date": cache_status['last_analysis'],
                    "moves": cached_moves
                }
            
            # Cache is stale or forcing refresh, generate new suggestions
            await websocket_manager.send_progress_update(
                property_code, 
                "generating", 
                "Cache is stale, generating new move suggestions...",
                progress=20.0
            )
            
            new_suggestions = await self._generate_new_suggestions(property_code, db)
            
            await websocket_manager.send_progress_update(
                property_code, 
                "completion", 
                f"Successfully generated {new_suggestions['move_count']} new move suggestions",
                progress=100.0,
                data=new_suggestions
            )
            
            return new_suggestions
            
        except Exception as e:
            # Handle the error more robustly to avoid string formatting issues
            try:
                error_detail = str(e) if e else "Unknown error"
            except:
                error_detail = "Unknown error (string conversion failed)"
            
            error_msg = f"Failed to get move suggestions for {property_code}: {error_detail}"
            logger.error(error_msg)
            
            await websocket_manager.send_error(
                property_code, 
                error_msg, 
                "suggestions_retrieval"
            )
            
            raise
    
    async def _check_cache_status(self, property_code: str, db: Session) -> Dict[str, Any]:
        """Check if cached suggestions are fresh (< 1 hour old)"""
        print(f"🔍 DEBUG: _check_cache_status called with property_code: {property_code!r}")
        print(f"🔍 DEBUG: property_code type: {type(property_code)}")
        print(f"🔍 DEBUG: property_code is None: {property_code is None}")
        
        logger.info(f"Checking cache status for {property_code}")
        
        # Get the latest analysis for this property
        latest_move = db.query(DefragMove).filter(
            DefragMove.property_code == property_code.upper()
        ).order_by(DefragMove.analysis_date.desc()).first()
        
        print(f"🔍 DEBUG: latest_move: {latest_move}")
        
        if not latest_move:
            print("🔍 DEBUG: No latest move found, returning no cache")
            return {
                "has_cache": False,
                "is_fresh": False,
                "last_analysis": None,
                "age_hours": None,
                "move_count": 0
            }
        
        print(f"🔍 DEBUG: latest_move.analysis_date: {latest_move.analysis_date}")
        print(f"🔍 DEBUG: latest_move.analysis_date type: {type(latest_move.analysis_date)}")
        
        # Calculate age
        now = datetime.now().replace(tzinfo=None)  # Make naive for comparison
        
        # Check if analysis_date exists and handle None case
        if latest_move.analysis_date is None:
            print("🔍 DEBUG: analysis_date is None, returning no cache")
            return {
                "has_cache": False,
                "is_fresh": False,
                "last_analysis": None,
                "age_hours": None,
                "move_count": latest_move.move_count or 0
            }
        
        analysis_date = latest_move.analysis_date.replace(tzinfo=None) if latest_move.analysis_date.tzinfo else latest_move.analysis_date
        age = now - analysis_date
        age_hours = age.total_seconds() / 3600
        is_fresh = age_hours < 1
        
        print(f"🔍 DEBUG: Calculated age_hours: {age_hours}")
        
        return {
            "has_cache": True,
            "is_fresh": is_fresh,
            "last_analysis": latest_move.analysis_date,
            "age_hours": age_hours,
            "move_count": latest_move.move_count
        }
    
    async def _get_cached_suggestions(self, property_code: str, db: Session) -> List[Dict[str, Any]]:
        """Get cached move suggestions from database"""
        logger.info(f"Retrieving cached suggestions for {property_code}")
        
        moves = db.query(DefragMove).filter(
            DefragMove.property_code == property_code.upper()
        ).order_by(DefragMove.analysis_date.desc()).all()
        
        return [self._move_to_dict(move) for move in moves]
    
    async def _generate_new_suggestions(self, property_code: str, db: Session) -> Dict[str, Any]:
        """Generate new move suggestions by calling RMS API"""
        logger.info(f"Generating new suggestions for {property_code}")
        
        await websocket_manager.send_progress_update(
            property_code, 
            "rms_connection", 
            "Connecting to RMS API...",
            progress=25.0
        )
        
        try:
            # Run the defragmentation analysis
            suggestions = await self._run_defragmentation_analysis(property_code, db)
            
            # Store the suggestions in database
            await websocket_manager.send_progress_update(
                property_code, 
                "storing", 
                f"Storing {len(suggestions)} suggestions in database...",
                progress=80.0
            )
            
            batch_info = await self._store_suggestions(property_code, suggestions, db)
            
            return {
                "move_count": len(suggestions),
                "is_cached": False,
                "cache_age_hours": 0.0,
                "analysis_date": datetime.now(),
                "moves": suggestions,
                "batch_info": batch_info
            }
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions for {property_code}: {e}")
            raise
    
    async def _run_defragmentation_analysis(self, property_code: str, db: Session) -> List[Dict[str, Any]]:
        """Run the actual defragmentation analysis"""
        logger.info(f"Running defragmentation analysis for {property_code}")
        
        await websocket_manager.send_progress_update(
            property_code, 
            "analysis_start", 
            "Starting defragmentation analysis...",
            progress=30.0
        )
        
        try:
            # For now, generate sample suggestions
            # In the real implementation, this would call the actual defragmentation logic
            await websocket_manager.send_progress_update(
                property_code, 
                "analysis_progress", 
                "Analyzing booking patterns and calculating strategic moves...",
                progress=50.0
            )
            
            # Simulate some processing time
            await asyncio.sleep(2)
            
            await websocket_manager.send_progress_update(
                property_code, 
                "analysis_complete", 
                "Analysis complete, generating move suggestions...",
                progress=70.0
            )
            
            # Generate sample suggestions (replace with actual logic)
            suggestions = await self._generate_sample_suggestions(property_code)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Analysis failed for {property_code}: {e}")
            raise
    
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
    
    async def _store_suggestions(self, property_code: str, suggestions: List[Dict[str, Any]], db: Session) -> Dict[str, Any]:
        """Store move suggestions in the database"""
        logger.info(f"Storing {len(suggestions)} suggestions for {property_code}")
        
        try:
            # Create a new batch for these suggestions
            batch = MoveBatch(
                property_code=property_code.upper(),
                status='completed',
                total_moves=len(suggestions),
                processed_moves=0,
                rejected_moves=0
            )
            db.add(batch)
            db.commit()
            db.refresh(batch)
            
            # Store each suggestion
            for suggestion in suggestions:
                move = DefragMove(
                    property_code=property_code.upper(),
                    property_id=1,  # This should be looked up from the property code
                    analysis_date=datetime.now(),
                    move_data=suggestion,
                    move_count=len(suggestions),
                    batch_id=batch.id,
                    is_processed=False,
                    is_rejected=False
                )
                db.add(move)
            
            db.commit()
            logger.info(f"Successfully stored {len(suggestions)} suggestions for {property_code}")
            
            # Return batch information
            return {
                "batch_id": batch.id,
                "total_moves": len(suggestions),
                "status": batch.status
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store suggestions for {property_code}: {e}")
            raise
    
    def _move_to_dict(self, move: DefragMove) -> Dict[str, Any]:
        """Convert DefragMove model to dictionary"""
        return {
            "id": move.id,
            "property_code": move.property_code,
            "analysis_date": move.analysis_date,
            "move_data": move.move_data,
            "move_count": move.move_count,
            "status": move.status,
            "batch_id": move.batch_id,
            "is_processed": move.is_processed,
            "is_rejected": move.is_rejected,
            "created_at": move.created_at
        }
    
    async def get_property_summary(self, property_code: str, db: Session) -> Dict[str, Any]:
        """Get summary of moves for a property"""
        logger.info(f"Getting property summary for {property_code}")
        
        # Get the latest analysis
        latest_move = db.query(DefragMove).filter(
            DefragMove.property_code == property_code.upper()
        ).order_by(DefragMove.analysis_date.desc()).first()
        
        if not latest_move:
            return {
                "property_code": property_code.upper(),
                "has_moves": False,
                "last_analysis": None,
                "total_moves": 0
            }
        
        # Get move counts by status
        total_moves = db.query(DefragMove).filter(
            DefragMove.property_code == property_code.upper()
        ).count()
        
        processed_moves = db.query(DefragMove).filter(
            DefragMove.property_code == property_code.upper(),
            DefragMove.is_processed == True
        ).count()
        
        rejected_moves = db.query(DefragMove).filter(
            DefragMove.property_code == property_code.upper(),
            DefragMove.is_rejected == True
        ).count()
        
        pending_moves = total_moves - processed_moves - rejected_moves
        
        return {
            "property_code": property_code.upper(),
            "has_moves": True,
            "last_analysis": latest_move.analysis_date,
            "total_moves": total_moves,
            "processed_moves": processed_moves,
            "rejected_moves": rejected_moves,
            "pending_moves": pending_moves
        }
    
    async def refresh_all_properties(self, db: Session) -> Dict[str, Any]:
        """Refresh move suggestions for all properties (admin only)"""
        logger.info("Refreshing move suggestions for all properties")
        
        # Get all properties
        properties = db.query(Property).all()
        total_properties = len(properties)
        refreshed = 0
        
        for property_obj in properties:
            try:
                await self.get_move_suggestions(property_obj.property_code, force_refresh=True, db=db)
                refreshed += 1
            except Exception as e:
                logger.error(f"Failed to refresh {property_obj.property_code}: {e}")
        
        return {
            "total_properties": total_properties,
            "refreshed": refreshed,
            "failed": total_properties - refreshed
        }
