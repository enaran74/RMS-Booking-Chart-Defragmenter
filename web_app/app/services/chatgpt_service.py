"""
ChatGPT service for generating move explanations
Uses OpenAI API to analyze booking charts and explain defragmentation rationale
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChatGPTService:
    """Service for integrating with OpenAI ChatGPT API to explain defragmentation moves"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o-mini"  # Using the latest efficient model
        
    def _is_configured(self) -> bool:
        """Check if ChatGPT API is properly configured"""
        return bool(self.api_key and self.api_key.startswith('sk-'))
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the ChatGPT API connection"""
        if not self._is_configured():
            return {
                "success": False,
                "message": "OpenAI API key not configured or invalid",
                "details": {"error": "API key missing or doesn't start with 'sk-'"}
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": "Hello, this is a test connection. Please respond with 'Connection successful'."}
                        ],
                        "max_tokens": 10
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "message": "ChatGPT API connection successful",
                        "details": {
                            "model": self.model,
                            "response": result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        }
                    }
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    return {
                        "success": False,
                        "message": f"ChatGPT API error: {response.status_code}",
                        "details": {"error": error_data.get("error", {}).get("message", "Unknown error")}
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "message": "ChatGPT API connection timeout",
                "details": {"error": "Request timed out after 30 seconds"}
            }
        except Exception as e:
            logger.error(f"ChatGPT API test error: {e}")
            return {
                "success": False,
                "message": "ChatGPT API connection failed",
                "details": {"error": str(e)}
            }
    
    def _format_move_data_for_analysis(self, moves_data: List[Dict], chart_data: Dict, property_code: str, category_filter: str = None) -> str:
        """Format move data and comprehensive chart context for ChatGPT analysis"""
        
        # Start with property and context
        formatted_data = f"PROPERTY: {property_code}\n"
        formatted_data += f"ANALYSIS PERIOD: {chart_data.get('start_date', 'N/A')} to {chart_data.get('end_date', 'N/A')}\n"
        
        if category_filter:
            formatted_data += f"ACCOMMODATION CATEGORY: {category_filter}\n"
        
        formatted_data += "\n"
        
        # Add comprehensive booking context from chart data, filtered by category
        if chart_data and chart_data.get("categories"):
            formatted_data += "CURRENT BOOKING SITUATION:\n"
            
            # Find units involved in moves
            involved_units = set()
            for move in moves_data:
                involved_units.add(move.get('from_unit_name', ''))
                involved_units.add(move.get('to_unit_name', ''))
            
            # Filter categories to target category only
            categories = chart_data.get("categories", [])
            target_categories = []
            
            if category_filter:
                # Exact match for category filtering
                target_categories = [cat for cat in categories if category_filter == cat.get("name", "")]
            else:
                target_categories = categories[:1]  # Just first category if no filter
            
            for category in target_categories:
                cat_name = category.get("name", "Unknown Category")
                units = category.get("units", [])
                
                formatted_data += f"\nCATEGORY: {cat_name}\n"
                formatted_data += f"This category has {len(units)} total units\n\n"
                
                # Show ALL units in this category with their booking status
                for unit in units[:10]:  # Limit to 10 units to avoid token overflow
                    unit_name = unit.get("unit_code", unit.get("name", "Unknown Unit"))
                    bookings = unit.get("bookings", [])
                    ooo_periods = unit.get("out_of_order", [])
                    
                    # Mark if this unit is involved in moves
                    is_involved = unit_name in involved_units
                    status_marker = "🔄 INVOLVED IN MOVES" if is_involved else "📋 Current Status"
                    
                    formatted_data += f"UNIT: {unit_name} ({status_marker})\n"
                    
                    # Add current bookings (FILTER OUT GHOST BOOKINGS)
                    if bookings:
                        # Filter out ghost bookings - only include real existing bookings
                        real_bookings = [
                            booking for booking in bookings 
                            if not booking.get("is_ghost_booking", False) 
                            and booking.get("status", "").lower() != "ghost"
                        ]
                        
                        if real_bookings:
                            formatted_data += f"  Existing Bookings:\n"
                            for booking in real_bookings[:5]:  # Show real bookings for context
                                guest = booking.get("guest_name", "Guest")
                                start = booking.get("start_date", "")
                                end = booking.get("end_date", "")
                                status = booking.get("status", "Confirmed")
                                formatted_data += f"    - {guest}: {start} to {end} ({status})\n"
                        else:
                            formatted_data += f"  Existing Bookings: NONE - Unit is available (ghost bookings filtered out)\n"
                    else:
                        formatted_data += f"  Existing Bookings: NONE - Unit is available\n"
                    
                    # Add out of order periods
                    if ooo_periods:
                        formatted_data += f"  Out of Order: "
                        for ooo in ooo_periods[:2]:
                            start = ooo.get("start_date", "")
                            end = ooo.get("end_date", "")
                            reason = ooo.get("reason", "Maintenance")
                            formatted_data += f"{start} to {end} ({reason}), "
                        formatted_data = formatted_data.rstrip(", ") + "\n"
                    
                    formatted_data += "\n"
        
        formatted_data += "PROPOSED DEFRAGMENTATION MOVES:\n"
        
        # Add detailed move analysis
        for i, move in enumerate(moves_data[:8], 1):  # Limit to 8 moves
            guest_name = move.get('guest_name', 'Guest')
            from_unit = move.get('from_unit_name', 'Unit')
            to_unit = move.get('to_unit_name', 'Unit')
            check_in = move.get('check_in', '')
            check_out = move.get('check_out', '')
            nights = move.get('nights', 0)
            nights_freed = move.get('nights_freed', 0)
            strategic_importance = move.get('strategic_importance_level', 'Medium')
            reason = move.get('reason', 'Optimization')
            is_holiday = move.get('is_holiday_move', False)
            holiday_period = move.get('holiday_period', '')
            
            formatted_data += f"\n{i}. MOVE: {guest_name}\n"
            formatted_data += f"   FROM: {from_unit} → TO: {to_unit}\n"
            formatted_data += f"   DATES: {check_in} to {check_out} ({nights} nights)\n"
            formatted_data += f"   NIGHTS FREED: {nights_freed}\n"
            formatted_data += f"   STRATEGIC IMPORTANCE: {strategic_importance}\n"
            formatted_data += f"   REASON: {reason}\n"
            
            if is_holiday and holiday_period:
                formatted_data += f"   HOLIDAY PERIOD: {holiday_period}\n"
        
        return formatted_data
    
    async def explain_moves(self, moves_data: List[Dict], chart_data: Dict, property_code: str, category_filter: str = None) -> Dict[str, Any]:
        """Generate explanation for defragmentation moves using ChatGPT"""
        
        if not self._is_configured():
            return {
                "success": False,
                "message": "ChatGPT API not configured. Please add your OpenAI API key in the Setup page.",
                "explanation": ""
            }
        
        if not moves_data:
            return {
                "success": False,
                "message": "No move suggestions available to explain",
                "explanation": ""
            }
        
        try:
            # Format the data for analysis
            formatted_data = self._format_move_data_for_analysis(moves_data, chart_data, property_code, category_filter)
            
            # LOG THE COMPLETE DATA BEING SENT TO CHATGPT
            logger.info("=" * 80)
            logger.info("CHATGPT REQUEST DEBUG - FULL DATA BEING SENT:")
            logger.info("=" * 80)
            logger.info(f"Property Code: {property_code}")
            logger.info(f"Number of moves: {len(moves_data)}")
            logger.info(f"Chart data keys: {list(chart_data.keys()) if chart_data else 'None'}")
            logger.info("Raw moves data:")
            for i, move in enumerate(moves_data[:3]):  # Log first 3 moves
                logger.info(f"  Move {i+1}: {move}")
            logger.info("Chart data structure:")
            if chart_data:
                if 'categories' in chart_data:
                    logger.info(f"  Categories count: {len(chart_data.get('categories', []))}")
                    for cat in chart_data.get('categories', [])[:2]:  # Log first 2 categories
                        logger.info(f"    Category: {cat.get('name', 'Unknown')}")
                        logger.info(f"      Units: {len(cat.get('units', []))}")
                        for unit in cat.get('units', [])[:2]:  # Log first 2 units
                            logger.info(f"        Unit: {unit.get('unit_code', unit.get('name', 'Unknown'))}")
                            logger.info(f"          Bookings: {len(unit.get('bookings', []))}")
            logger.info("FORMATTED DATA FOR CHATGPT:")
            logger.info("-" * 40)
            logger.info(formatted_data)
            logger.info("=" * 80)
            
            # Create the prompt
            prompt = f"""You are a senior revenue manager at a large accommodation provider analyzing defragmentation moves for a specific accommodation category. Use the complete booking data provided to evaluate each suggested move.

{formatted_data}

BOOKING MOVEMENT CONSTRAINTS:
Only reservations meeting ALL these criteria can be moved:
• STATUS: Only "Confirmed" or "Unconfirmed" bookings (NOT Pencil, Maintenance, Arrived, Departed, Owner Occupied, Quote)
• FIXED STATUS: Reservations marked as "fixed" in RMS are never moved (protects VIP bookings, special arrangements)
• ANALYSIS PERIOD: Entire stay must fall within the constraint date range (no partial overlaps)
• CATEGORY: Moves only occur within the same accommodation category
• AVAILABILITY: Target unit must be completely available for entire stay period
• IMPROVEMENT: Only moves that demonstrably improve fragmentation scores are suggested

ANALYSIS CONTEXT:
• These move suggestions were generated by analyzing ALL units in this accommodation category simultaneously
• The algorithm considered the entire category's booking patterns, not just individual unit pairs
• Moves are ranked by strategic importance and potential fragmentation reduction
• The goal is creating longer contiguous availability blocks that exponentially increase revenue potential
• Sequential moves may be interdependent - earlier moves can affect the viability of later moves

CRITICAL ANALYSIS APPROACH:
1. Evaluate the COMPLETE SEQUENCE of all proposed moves as they would be implemented in order
2. Consider the cumulative effect across the entire category after all moves are completed
3. Analyze how each move contributes to the overall defragmentation strategy
4. Assess whether the final result optimizes the category's booking potential

ANALYSIS INSTRUCTIONS:
For each proposed move, examine:
   - Current booking patterns in BOTH source and target units
   - How this move fits into the broader category optimization strategy
   - The cumulative impact when combined with other proposed moves
   - Whether conflicts exist that would prevent successful implementation
   - The final availability pattern after ALL moves are completed

Consider the business impact:
   - Does the complete sequence create meaningful contiguous blocks for future bookings?
   - How does this move contribute to overall category defragmentation?
   - What is the revenue optimization potential of the final arrangement?

Please provide your analysis in this format:

### 1. Sequential Move Analysis:

For each move, provide:
- **Current Situation**: Booking patterns in source and target units before any moves
- **Move Impact**: How this specific move changes availability patterns
- **Cumulative Effect**: Combined impact with other moves in the sequence
- **Strategic Value**: Contribution to overall category optimization

### 2. Overall Assessment:

Evaluate the complete move sequence:
- ✅ **Highly Beneficial**: Significant improvement to category utilization
- ⚠️ **Moderate Benefit**: Some improvement but with considerations
- ❌ **Problematic**: Conflicts or minimal benefit

### 3. Final Recommendation:

Provide a summary assessment of whether implementing this complete sequence of moves would optimize the category's revenue potential, referencing specific booking patterns and final availability blocks that would be created.

Reference specific guest names, units, dates, and the sequential order of moves in your analysis."""

            # LOG THE COMPLETE PROMPT
            logger.info("COMPLETE CHATGPT PROMPT:")
            logger.info("-" * 60)
            logger.info(prompt)
            logger.info("-" * 60)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 4000,
                        "temperature": 0.7
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    explanation = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    
                    return {
                        "success": True,
                        "message": "Move explanation generated successfully",
                        "explanation": explanation,
                        "moves_analyzed": len(moves_data),
                        "property_code": property_code
                    }
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    
                    return {
                        "success": False,
                        "message": f"ChatGPT API error: {error_message}",
                        "explanation": ""
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "message": "ChatGPT API request timed out. Please try again.",
                "explanation": ""
            }
        except Exception as e:
            logger.error(f"ChatGPT explanation error: {e}")
            return {
                "success": False,
                "message": f"Error generating explanation: {str(e)}",
                "explanation": ""
            }

# Global instance
chatgpt_service = ChatGPTService()
