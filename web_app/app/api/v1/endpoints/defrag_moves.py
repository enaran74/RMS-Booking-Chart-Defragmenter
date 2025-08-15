"""
Defragmentation moves endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.defrag_move import DefragMove
from app.schemas.defrag_move import DefragMoveCreate, DefragMoveResponse, DefragMoveUpdate, DefragMoveApproval
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[DefragMoveResponse])
async def get_defrag_moves(
    property_id: int = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get defragmentation moves with optional filtering"""
    query = db.query(DefragMove)
    
    if property_id:
        query = query.filter(DefragMove.property_id == property_id)
    
    if status:
        query = query.filter(DefragMove.status == status)
    
    # If user is not admin, only show moves for their property
    if not current_user.is_admin and current_user.property_id:
        query = query.filter(DefragMove.property_id == current_user.property_id)
    
    moves = query.order_by(DefragMove.created_at.desc()).all()
    return [DefragMoveResponse.model_validate(move) for move in moves]

@router.get("/{move_id}", response_model=DefragMoveResponse)
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
    if not current_user.is_admin and current_user.property_id != move.property_id:
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
    if not current_user.is_admin and current_user.property_id != move_data.property_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db_move = DefragMove(
        property_id=move_data.property_id,
        move_data=move_data.move_data,
        suggested_by=current_user.username
    )
    
    db.add(db_move)
    db.commit()
    db.refresh(db_move)
    
    return DefragMoveResponse.model_validate(db_move)

@router.put("/{move_id}/approve")
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
    if not current_user.is_admin and current_user.property_id != move.property_id:
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
    
    return {"message": f"Move {approval_data.action}d successfully", "move_id": move_id}

@router.delete("/{move_id}")
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
    
    return {"message": "Move deleted successfully"}
