"""
Defragmentation moves endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.defrag_move import DefragMove
from app.models.property import Property
from app.models.move_batch import MoveBatch
from app.schemas.defrag_move import (
    DefragMoveCreate, DefragMoveResponse, DefragMoveUpdate, 
    DefragMoveApproval, DefragMoveSummary, DefragMoveDetail
)
from app.services.defrag_service import DefragService
from datetime import datetime, timedelta
import logging
from app.core.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the defrag service
defrag_service = DefragService()

@router.get("/", response_model=List[DefragMoveResponse])
async def get_defrag_moves(
    property_id: Optional[int] = Query(None, description="Filter by property ID"),
    property_code: Optional[str] = Query(None, description="Filter by property code"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get defragmentation moves with optional filtering and pagination"""
    query = db.query(DefragMove)
    
    # Apply filters
    if property_id:
        query = query.filter(DefragMove.property_id == property_id)
    
    if property_code:
        query = query.filter(DefragMove.property_code == property_code.upper())
    
    if status:
        query = query.filter(DefragMove.status == status)
    
    # If user is not admin, only show moves for their assigned properties
    if not current_user.is_admin:
        # Get user's assigned properties
        from app.models.user_property import UserProperty
        user_properties = db.query(UserProperty).filter(UserProperty.user_id == current_user.id).all()
        if user_properties:
            property_ids = [up.property_id for up in user_properties]
            query = query.filter(DefragMove.property_id.in_(property_ids))
        else:
            # User has no properties assigned, return empty list
            return []
    
    # Apply pagination and ordering
    moves = query.order_by(DefragMove.analysis_date.desc(), DefragMove.created_at.desc()).offset(offset).limit(limit).all()
    
    return [DefragMoveResponse.model_validate(move) for move in moves]

@router.get("/summary", response_model=List[DefragMoveSummary])
async def get_defrag_moves_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary of defragmentation moves for all properties"""
    # Get the latest analysis for each property
    subquery = db.query(
        DefragMove.property_id,
        DefragMove.analysis_date,
        DefragMove.move_count,
        DefragMove.status,
        DefragMove.updated_at
    ).distinct(DefragMove.property_id).order_by(
        DefragMove.property_id, 
        DefragMove.analysis_date.desc()
    ).subquery()
    
    query = db.query(
        subquery.c.property_id,
        subquery.c.analysis_date,
        subquery.c.move_count,
        subquery.c.status,
        subquery.c.updated_at,
        Property.property_code,
        Property.property_name
    ).join(Property, subquery.c.property_id == Property.id)
    
    # If user is not admin, only show their assigned properties
    if not current_user.is_admin:
        from app.models.user_property import UserProperty
        user_properties = db.query(UserProperty).filter(UserProperty.user_id == current_user.id).all()
        if user_properties:
            property_ids = [up.property_id for up in user_properties]
            query = query.filter(Property.id.in_(property_ids))
        else:
            return []
    
    results = query.all()
    
    summaries = []
    for result in results:
        summaries.append(DefragMoveSummary(
            property_code=result.property_code,
            property_name=result.property_name,
            analysis_date=result.analysis_date,
            move_count=result.move_count,
            status=result.status,
            last_updated=result.updated_at
        ))
    
    return summaries

@router.get("/cache-status/{property_code}")
async def get_cache_status(
    property_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if move suggestions cache is fresh (< 1 hour old) for a property"""
    # Check if user has access to this property
    if not current_user.is_admin:
        from app.models.user_property import UserProperty
        user_property = db.query(UserProperty).filter(
            UserProperty.user_id == current_user.id,
            UserProperty.property_id == Property.id
        ).join(Property, Property.property_code == property_code.upper()).first()
        
        if not user_property:
            raise HTTPException(status_code=403, detail="Access denied to this property")
    
    # Validate that the property exists
    property_obj = db.query(Property).filter(Property.property_code == property_code.upper()).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail=f"Property {property_code.upper()} not found")
    
    # Get the latest analysis for this property
    latest_move = db.query(DefragMove).filter(
        DefragMove.property_code == property_code.upper()
    ).order_by(DefragMove.analysis_date.desc()).first()
    
    if not latest_move:
        return {
            "property_code": property_code.upper(),
            "has_cache": False,
            "is_fresh": False,
            "last_analysis": None,
            "age_hours": None,
            "move_count": 0
        }
    
    # Calculate age
    now = datetime.now().replace(tzinfo=None)  # Make naive for comparison
    analysis_date = latest_move.analysis_date.replace(tzinfo=None) if latest_move.analysis_date.tzinfo else latest_move.analysis_date
    age = now - analysis_date
    age_hours = age.total_seconds() / 3600
    is_fresh = age_hours < 1
    
    return {
        "property_code": property_code.upper(),
        "has_cache": True,
        "is_fresh": is_fresh,
        "last_analysis": latest_move.analysis_date,
        "age_hours": round(age_hours, 2),
        "move_count": latest_move.move_count
    }

@router.post("/generate/{property_code}")
async def generate_move_suggestions(
    property_code: str,
    force_refresh: bool = Query(False, description="Force generation of new suggestions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate move suggestions for a specific property by calling RMS API"""
    print(f"🌟🌟🌟 ENDPOINT generate_move_suggestions CALLED FOR {property_code} 🌟🌟🌟")
    logger.info(f"🌟 ENDPOINT generate_move_suggestions CALLED FOR {property_code}")
    logger.info(f"Generating move suggestions for {property_code} (force_refresh: {force_refresh})")
    
    # Check if user has access to this property
    if not current_user.is_admin:
        from app.models.user_property import UserProperty
        user_property = db.query(UserProperty).filter(
            UserProperty.user_id == current_user.id,
            UserProperty.property_id == Property.id
        ).join(Property, Property.property_code == property_code.upper()).first()
        
        if not user_property:
            raise HTTPException(status_code=403, detail="Access denied to this property")
    
    # Validate that the property exists
    property_obj = db.query(Property).filter(Property.property_code == property_code.upper()).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail=f"Property {property_code.upper()} not found")
    
    try:
        # Create a new batch for this generation
        batch = MoveBatch(
            property_code=property_code.upper(),
            created_by=current_user.id,
            status='processing',
            total_moves=0,
            processed_moves=0,
            rejected_moves=0
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        
        logger.info(f"Created batch {batch.id} for {property_code}")
        
        # Send batch creation update via WebSocket
        await websocket_manager.send_progress_update(
            property_code.upper(),
            "batch_created",
            f"Created batch {batch.id} for move generation",
            progress=5.0,
            data={"batch_id": batch.id}
        )
        
        # Use the defrag service to generate suggestions (this will send WebSocket updates)
        suggestions = await defrag_service.get_move_suggestions(
            property_code, 
            force_refresh=force_refresh, 
            db=db
        )
        
        # Update batch with move count
        batch.total_moves = suggestions["move_count"]
        batch.status = 'completed'
        db.commit()
        
        # Update all generated moves to link to this batch
        if suggestions.get("moves"):
            for move in suggestions["moves"]:
                # Since move is a dictionary, we need to update the database record directly
                # The move dictionary contains the move data, but we need to update the actual database record
                if "id" in move:
                    db_move = db.query(DefragMove).filter(DefragMove.id == move["id"]).first()
                    if db_move:
                        db_move.batch_id = batch.id
            db.commit()
        
        # Send completion update via WebSocket
        await websocket_manager.send_completion(
            property_code.upper(),
            {
                "batch_id": batch.id,
                "move_count": suggestions["move_count"],
                "status": "completed"
            }
        )
        
        logger.info(f"Successfully generated {suggestions['move_count']} suggestions for {property_code} in batch {batch.id}")
        
        # Return the fresh suggestions directly from the generation
        return {
            "success": True,
            "property_code": property_code.upper(),
            "batch_id": batch.id,
            "move_count": suggestions["move_count"],
            "is_cached": suggestions["is_cached"],
            "cache_age_hours": suggestions["cache_age_hours"],
            "analysis_date": suggestions["analysis_date"],
            "moves": suggestions.get("moves", []),  # Include the actual fresh suggestions
            "batch_info": {
                "batch_id": batch.id,
                "created_at": batch.created_at,
                "status": batch.status,
                "total_moves": batch.total_moves,
                "processed_moves": batch.processed_moves,
                "rejected_moves": batch.rejected_moves
            },
            "message": f"Generated {suggestions['move_count']} move suggestions for {property_code} in batch {batch.id}"
        }
        
    except Exception as e:
        # Update batch status to failed if it exists
        if 'batch' in locals():
            batch.status = 'failed'
            db.commit()
            
            # Send error update via WebSocket
            await websocket_manager.send_error(
                property_code.upper(),
                str(e),
                "generation_failed"
            )
        
        error_msg = f"Failed to generate suggestions for {property_code}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/refresh-all")
async def refresh_all_properties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refresh move suggestions for all properties (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logger.info("Admin user requested refresh of all properties")
    
    try:
        # Use the defrag service to refresh all properties
        results = await defrag_service.refresh_all_properties(db)
        
        logger.info(f"Refresh completed: {results['refreshed']}/{results['total_properties']} properties refreshed")
        
        return {
            "success": True,
            "message": f"Refreshed {results['refreshed']}/{results['total_properties']} properties",
            "results": results
        }
        
    except Exception as e:
        error_msg = f"Failed to refresh all properties: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/suggestions/{property_code}")
async def get_move_suggestions(
    property_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get move suggestions for a property from database only (no RMS API calls)"""
    logger.info(f"Getting move suggestions for {property_code} from database")
    
    # Check if user has access to this property
    if not current_user.is_admin:
        from app.models.user_property import UserProperty
        user_property = db.query(UserProperty).filter(
            UserProperty.user_id == current_user.id,
            UserProperty.property_id == Property.id
        ).join(Property, Property.property_code == property_code.upper()).first()
        
        if not user_property:
            raise HTTPException(status_code=403, detail="Access denied to this property")
    
    # Validate that the property exists
    property_obj = db.query(Property).filter(Property.property_code == property_code.upper()).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail=f"Property {property_code.upper()} not found")
    
    # Get the most recent batch for this property
    from app.models.move_batch import MoveBatch
    latest_batch = db.query(MoveBatch).filter(
        MoveBatch.property_code == property_code.upper()
    ).order_by(MoveBatch.created_at.desc()).first()
    
    if not latest_batch:
        logger.info(f"No batches found for property {property_code}")
        moves = []
    else:
        # Only get move suggestions from the most recent batch
        moves = db.query(DefragMove).filter(
            DefragMove.property_code == property_code.upper(),
            DefragMove.batch_id == latest_batch.id,
            DefragMove.is_processed == False,
            DefragMove.is_rejected == False
        ).order_by(DefragMove.analysis_date.desc(), DefragMove.created_at.desc()).all()
        
        logger.info(f"Found latest batch {latest_batch.id} for {property_code} with {len(moves)} unprocessed suggestions")
    
    # Get batch information if available
    batch_info = None
    if latest_batch:
        batch_info = {
            "batch_id": latest_batch.id,
            "created_at": latest_batch.created_at,
            "status": latest_batch.status,
            "total_moves": latest_batch.total_moves,
            "processed_moves": latest_batch.processed_moves,
            "rejected_moves": latest_batch.rejected_moves
        }
    
    logger.info(f"Retrieved {len(moves)} unprocessed suggestions for {property_code}")
    
    # Extract individual move suggestions from move_data.moves
    individual_moves = []
    for move_record in moves:
        if move_record.move_data and 'moves' in move_record.move_data:
            for individual_move in move_record.move_data['moves']:
                # Normalize field names for frontend consistency
                normalized_move = {
                    # Core move data with consistent field names
                    'from_unit': individual_move.get('current_unit', individual_move.get('from_unit', '')),
                    'to_unit': individual_move.get('target_unit', individual_move.get('to_unit', '')),
                    'guest': individual_move.get('guest_name', individual_move.get('guest', '')),
                    'reservation_id': individual_move.get('reservation_id', ''),
                    'check_in': individual_move.get('check_in', ''),
                    'check_out': individual_move.get('check_out', ''),
                    'category': individual_move.get('category', 'Uncategorized'),
                    'strategic_importance': individual_move.get('strategic_importance', 'Medium'),
                    'score': individual_move.get('score', 0),
                    'sequential_order': individual_move.get('sequential_order', ''),
                    'reason': individual_move.get('reason', 'Defragmentation optimization'),
                    'nights_freed': individual_move.get('nights_freed', 1),
                    # Metadata
                    'move_id': move_record.id,
                    'batch_id': move_record.batch_id,
                    'analysis_date': move_record.analysis_date.isoformat(),
                    'id': f"{move_record.id}_{len(individual_moves)}"  # Unique ID for frontend
                }
                individual_moves.append(normalized_move)
    
    logger.info(f"Extracted {len(individual_moves)} individual move suggestions for {property_code}")
    
    return {
        "success": True,
        "property_code": property_code.upper(),
        "move_count": len(individual_moves),
        "batch_info": batch_info,
        "moves": individual_moves
    }

@router.get("/id/{move_id}", response_model=DefragMoveResponse)
async def get_defrag_move(
    move_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific defragmentation move"""
    move = db.query(DefragMove).filter(DefragMove.id == move_id).first()
    
    if not move:
        raise HTTPException(status_code=404, detail="Move not found")
    
    # Check if user has access to this move
    if not current_user.is_admin:
        from app.models.user_property import UserProperty
        user_property = db.query(UserProperty).filter(
            UserProperty.user_id == current_user.id,
            UserProperty.property_id == move.property_id
        ).first()
        
        if not user_property:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return DefragMoveResponse.model_validate(move)

@router.post("/", response_model=DefragMoveResponse)
async def create_defrag_move(
    move_data: DefragMoveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new defragmentation move suggestion"""
    # Check if user has access to the property
    if not current_user.is_admin:
        from app.models.user_property import UserProperty
        user_property = db.query(UserProperty).filter(
            UserProperty.user_id == current_user.id,
            UserProperty.property_id == move_data.property_id
        ).first()
        
        if not user_property:
            raise HTTPException(status_code=403, detail="Access denied to this property")
    
    # Validate property exists
    property_obj = db.query(Property).filter(Property.id == move_data.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Ensure property_code matches
    if move_data.property_code.upper() != property_obj.property_code:
        raise HTTPException(status_code=400, detail="Property code mismatch")
    
    db_move = DefragMove(
        property_id=move_data.property_id,
        property_code=move_data.property_code.upper(),
        analysis_date=move_data.analysis_date,
        move_data=move_data.move_data,
        move_count=move_data.move_count,
        suggested_by=current_user.username
    )
    
    db.add(db_move)
    db.commit()
    db.refresh(db_move)
    
    logger.info(f"Created defrag move for property {move_data.property_code}: {move_data.move_count} moves")
    return DefragMoveResponse.model_validate(db_move)

@router.put("/id/{move_id}/approve")
async def approve_defrag_move(
    move_id: int,
    approval_data: DefragMoveApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject a defragmentation move"""
    move = db.query(DefragMove).filter(DefragMove.id == move_id).first()
    
    if not move:
        raise HTTPException(status_code=404, detail="Move not found")
    
    # Check if user has access to this move
    if not current_user.is_admin:
        from app.models.user_property import UserProperty
        user_property = db.query(UserProperty).filter(
            UserProperty.user_id == current_user.id,
            UserProperty.property_id == move.property_id
        ).first()
        
        if not user_property:
            raise HTTPException(status_code=403, detail="Access denied")
    
    if approval_data.action == "approve":
        move.status = "approved"
        move.approved_by = current_user.username
        move.approved_at = datetime.utcnow()
    elif approval_data.action == "reject":
        move.status = "rejected"
        move.approved_by = current_user.username
        move.approved_at = datetime.utcnow()
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    db.commit()
    db.refresh(move)
    
    logger.info(f"Move {move_id} {approval_data.action}d by {current_user.username}")
    return {"message": f"Move {approval_data.action}d successfully", "move_id": move_id}

@router.delete("/id/{move_id}")
async def delete_defrag_move(
    move_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a defragmentation move (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    move = db.query(DefragMove).filter(DefragMove.id == move_id).first()
    
    if not move:
        raise HTTPException(status_code=404, detail="Move not found")
    
    db.delete(move)
    db.commit()
    
    logger.info(f"Move {move_id} deleted by admin {current_user.username}")
    return {"message": "Move deleted successfully"}

@router.post("/process")
async def process_selected_moves(
    move_actions: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process selected moves (accept or reject)"""
    logger.info(f"Processing {len(move_actions)} moves")
    
    if not move_actions:
        raise HTTPException(status_code=400, detail="No moves to process")
    
    processed_moves = []
    rejected_moves = []
    
    try:
        for action in move_actions:
            move_id = action.get("move_id")
            action_type = action.get("action")  # "accept" or "reject"
            
            if not move_id or action_type not in ["accept", "reject"]:
                continue
            
            # Get the move
            move = db.query(DefragMove).filter(DefragMove.id == move_id).first()
            if not move:
                continue
            
            # Check if user has access to this move
            if not current_user.is_admin:
                from app.models.user_property import UserProperty
                user_property = db.query(UserProperty).filter(
                    UserProperty.user_id == current_user.id,
                    UserProperty.property_id == move.property_id
                ).first()
                
                if not user_property:
                    continue
            
            # Process the move
            if action_type == "accept":
                move.is_processed = True
                move.processed_at = datetime.now()
                move.processed_by = current_user.id
                move.status = "approved"
                processed_moves.append(move_id)
                
                # Update batch statistics if available
                if move.batch_id:
                    batch = db.query(MoveBatch).filter(MoveBatch.id == move.batch_id).first()
                    if batch:
                        batch.processed_moves += 1
                
            elif action_type == "reject":
                move.is_rejected = True
                move.rejected_at = datetime.now()
                move.rejected_by = current_user.id
                move.status = "rejected"
                rejected_moves.append(move_id)
                
                # Update batch statistics if available
                if move.batch_id:
                    batch = db.query(MoveBatch).filter(MoveBatch.id == move.batch_id).first()
                    if batch:
                        batch.rejected_moves += 1
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Successfully processed {len(processed_moves)} moves and rejected {len(rejected_moves)} moves")
        
        return {
            "success": True,
            "processed_moves": processed_moves,
            "rejected_moves": rejected_moves,
            "total_processed": len(processed_moves),
            "total_rejected": len(rejected_moves),
            "message": f"Processed {len(processed_moves)} moves and rejected {len(rejected_moves)} moves"
        }
        
    except Exception as e:
        db.rollback()
        error_msg = f"Failed to process moves: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/test-endpoint")
async def test_endpoint():
    """BRAND NEW TEST - completely different route"""
    return {"test": "success", "message": "New test endpoint works"}

@router.get("/history")
async def get_move_history(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    property_code: Optional[str] = Query(None, description="Filter by property code"),
    status: Optional[str] = Query(None, description="Filter by status (processed, rejected, pending)"),
    limit: int = Query(100, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get move history with date range filtering and pagination"""
    logger.info(
        f"Getting move history for user {current_user.username} with params: "
        f"start_date={start_date}, end_date={end_date}, property_code={property_code}, "
        f"status={status}, limit={limit}, offset={offset}"
    )

    try:
        # Build base query
        query = db.query(DefragMove)

        # Filters
        if property_code:
            query = query.filter(DefragMove.property_code == property_code.upper())

        if status:
            if status == "processed":
                query = query.filter(DefragMove.is_processed == True)
            elif status == "rejected":
                query = query.filter(DefragMove.is_rejected == True)
            elif status == "pending":
                query = query.filter(DefragMove.is_processed == False, DefragMove.is_rejected == False)

        # Date filters
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(DefragMove.analysis_date >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(DefragMove.analysis_date < end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

        # Default date range: last 7 days
        if not start_date and not end_date:
            default_start = datetime.now() - timedelta(days=7)
            query = query.filter(DefragMove.analysis_date >= default_start)

        # Restrict to user's properties if not admin
        if not current_user.is_admin:
            from app.models.user_property import UserProperty
            user_properties = db.query(UserProperty).filter(UserProperty.user_id == current_user.id).all()
            if user_properties:
                property_ids = [up.property_id for up in user_properties]
                query = query.filter(DefragMove.property_id.in_(property_ids))
            else:
                return {
                    "success": True,
                    "total_count": 0,
                    "moves": [],
                    "pagination": {
                        "limit": limit,
                        "offset": offset,
                        "has_more": False
                    }
                }

        total_count = query.count()

        moves = (
            query.order_by(DefragMove.analysis_date.desc(), DefragMove.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        move_responses = []
        for move in moves:
            move_data = DefragMoveResponse.model_validate(move)
            history_info = {
                "move_id": move.id,
                "property_code": move.property_code,
                "analysis_date": move.analysis_date,
                "move_data": move.move_data,
                "strategic_importance": move.move_data.get("strategic_importance", "N/A") if move.move_data else "N/A",
                "score": move.move_data.get("score", "N/A") if move.move_data else "N/A",
                "status": move.status,
                "is_processed": move.is_processed,
                "is_rejected": move.is_rejected,
                "processed_at": move.processed_at,
                "rejected_at": move.rejected_at,
                "batch_id": move.batch_id,
                "created_at": move.created_at,
            }
            move_responses.append(history_info)

        logger.info(f"Retrieved {len(moves)} moves from history for user {current_user.username}")

        return {
            "success": True,
            "total_count": total_count,
            "moves": move_responses,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
            },
        }
    except Exception as e:
        logger.error(f"Error in get_move_history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving move history: {str(e)}")
