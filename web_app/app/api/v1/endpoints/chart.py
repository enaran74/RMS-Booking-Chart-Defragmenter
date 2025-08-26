#!/usr/bin/env python3
"""
Chart API endpoints
Provides booking chart data for visual representation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.chart_service_new import BookingChartService

router = APIRouter()


@router.get("/booking-chart/{property_code}")
async def get_booking_chart(
    property_code: str,
    refresh: Optional[bool] = Query(False, description="Force refresh chart data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get visual booking chart data for a property
    
    Args:
        property_code: Property code (e.g., 'CALI')
        refresh: Whether to force refresh the data
        
    Returns:
        Structured chart data for frontend rendering
    """
    try:
        chart_service = BookingChartService()
        
        # Get chart data
        chart_data = await chart_service.get_chart_data_for_property(property_code)
        
        if not chart_data:
            raise HTTPException(
                status_code=404, 
                detail=f"No chart data available for property {property_code}. "
                       "Please run defragmentation analysis first."
            )
        
        return {
            "success": True,
            "data": chart_data,
            "message": f"Chart data retrieved for property {property_code}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chart data: {str(e)}"
        )


@router.get("/booking-chart/{property_code}/categories")
async def get_chart_categories(
    property_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get accommodation categories for a property (lightweight endpoint)
    
    Args:
        property_code: Property code
        
    Returns:
        List of accommodation categories
    """
    try:
        chart_service = BookingChartService()
        
        # Get chart data
        chart_data = await chart_service.get_chart_data_for_property(property_code)
        
        if not chart_data:
            return {
                "success": True,
                "data": {"categories": []},
                "message": f"No categories found for property {property_code}"
            }
        
        # Extract just category names
        categories = [
            {
                "name": cat["name"],
                "unit_count": len(cat["units"])
            }
            for cat in chart_data.get("categories", [])
        ]
        
        return {
            "success": True,
            "data": {"categories": categories},
            "message": f"Categories retrieved for property {property_code}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving categories: {str(e)}"
        )
