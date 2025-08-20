#!/usr/bin/env python3
"""
Proper Defragmentation Analyzer for Web App
Based on the original defrag_analyzer.py logic but adapted for web environment
"""

import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any
import asyncio

logger = logging.getLogger(__name__)

class ProperDefragAnalyzer:
    def __init__(self):
        """Initialize the proper defragmentation analyzer"""
        logger.info("ProperDefragAnalyzer initialized")
        
    def analyze_defragmentation_opportunities(self, reservations: List[Dict], units: List[Dict], 
                                           property_code: str, constraint_start_date=None, constraint_end_date=None) -> List[Dict[str, Any]]:
        """
        Perform proper defragmentation analysis following original algorithm
        
        Args:
            reservations: List of reservation dictionaries from RMS API
            units: List of unit/area dictionaries from RMS API  
            property_code: Property code for analysis
            
        Returns:
            List of move suggestion dictionaries
        """
        logger.info(f"Starting proper defragmentation analysis for {property_code}")
        logger.info(f"Input data: {len(reservations)} reservations, {len(units)} units")
        
        # Step 1: Set constraint dates (use provided dates or default to 31 days to match original)
        if constraint_start_date is None:
            constraint_start_date = datetime.now().date()
        if constraint_end_date is None:
            constraint_end_date = constraint_start_date + timedelta(days=31)
        
        logger.info(f"Analysis period: {constraint_start_date} to {constraint_end_date}")
        
        # Step 2: Convert data to proper format
        reservations_data = self._convert_reservations_format(reservations)
        inventory_data = self._convert_inventory_format(units)
        
        logger.info(f"Converted data: {len(reservations_data)} reservations, {len(inventory_data)} units")
        
        if not reservations_data or not inventory_data:
            logger.warning("Insufficient data for analysis")
            return []
        
        # Step 3: Build occupancy matrix
        logger.info("Building occupancy matrix...")
        occupancy, dates, units_by_category = self._calculate_occupancy_matrix(
            reservations_data, inventory_data, constraint_start_date, constraint_end_date
        )
        
        # Step 4: Calculate strategic importance for categories
        logger.info("Calculating strategic importance...")
        category_importance = self._calculate_category_strategic_importance(
            reservations_data, inventory_data, constraint_start_date, constraint_end_date,
            occupancy, dates, units_by_category
        )
        
        # Step 5: Find move suggestions
        logger.info("Finding move suggestions...")
        suggestions = self._suggest_moves(
            reservations_data, inventory_data, occupancy, dates, units_by_category,
            category_importance, constraint_start_date, constraint_end_date
        )
        
        logger.info(f"Generated {len(suggestions)} move suggestions")
        return suggestions
    
    def _convert_reservations_format(self, reservations: List[Dict]) -> List[Dict]:
        """Convert RMS API reservation format to internal format"""
        converted = []
        
        logger.info(f"Converting {len(reservations)} reservations from RMS format")
        
        # Debug: Log first few reservations to understand structure
        if reservations:
            logger.info(f"Sample reservation keys: {list(reservations[0].keys())}")
            logger.info(f"Sample reservation data: {reservations[0]}")
        
        for i, res in enumerate(reservations):
            try:
                # Debug log for first few reservations
                if i < 3:
                    logger.info(f"Converting reservation {i}: {res}")
                
                # Parse dates properly - RMS API uses arrivalDate/departureDate  
                check_in = res.get('arrivalDate') or res.get('checkIn') or res.get('arrive') or res.get('checkInDate', '')
                check_out = res.get('departureDate') or res.get('checkOut') or res.get('depart') or res.get('checkOutDate', '')
                # RMS API uses areaName for unit identifier
                unit_code = res.get('areaName') or res.get('unitCode') or res.get('unit') or res.get('roomCode') or res.get('areaCode', '')
                
                logger.debug(f"Reservation {i}: check_in={check_in}, check_out={check_out}, unit={unit_code}")
                
                if check_in and check_out and unit_code:
                    converted_res = {
                        'Arrive': check_in[:10] if isinstance(check_in, str) else str(check_in)[:10],  # YYYY-MM-DD format
                        'Depart': check_out[:10] if isinstance(check_out, str) else str(check_out)[:10],
                        'Unit/Site': unit_code,
                        'firstName': res.get('guestGiven') or res.get('firstName') or res.get('guestFirstName', 'Guest'),
                        'lastName': res.get('guestSurname') or res.get('lastName') or res.get('guestLastName', ''),
                        'reservationId': res.get('id') or res.get('reservationId', ''),
                        'category': res.get('categoryName') or res.get('unitCategory') or res.get('category') or res.get('roomType', 'Unknown'),
                        'status': res.get('status', ''),
                        'guests': (res.get('adults', 0) or 0) + (res.get('children', 0) or 0),
                        'is_fixed': self._is_reservation_fixed(res)
                    }
                    converted.append(converted_res)
                    if i < 3:
                        logger.info(f"Successfully converted reservation {i}: {converted_res}")
                else:
                    if i < 10:  # Log first 10 failed conversions
                        logger.warning(f"Skipping reservation {i} - missing required fields: check_in={check_in}, check_out={check_out}, unit={unit_code}")
                        
            except Exception as e:
                if i < 10:  # Log first 10 errors
                    logger.error(f"Error converting reservation {i}: {e}")
                continue
        
        logger.info(f"Conversion complete: {len(converted)} out of {len(reservations)} reservations converted")
        return converted
    
    def _convert_inventory_format(self, units: List[Dict]) -> List[Dict]:
        """Convert RMS API unit format to internal format"""
        converted = []
        
        logger.info(f"Converting {len(units)} units from RMS format")
        
        # Debug: Log first few units to understand structure
        if units:
            logger.info(f"Sample unit keys: {list(units[0].keys())}")
            logger.info(f"Sample unit data: {units[0]}")
        
        for i, unit in enumerate(units):
            try:
                # Debug log for first few units
                if i < 3:
                    logger.info(f"Converting unit {i}: {unit}")
                
                # RMS API uses 'name' for unit code (e.g., 'SCLA-01')
                unit_code = unit.get('name') or unit.get('areaCode') or unit.get('unitCode') or unit.get('code', '')
                # Category needs to be looked up from categoryId
                category = unit.get('categoryCode') or unit.get('category') or unit.get('unitCategory') or f"Category_{unit.get('categoryId', 'Unknown')}"
                
                if unit_code:
                    converted_unit = {
                        'Unit/Site': unit_code,
                        'Category': category,
                        'Type': unit.get('areaType') or unit.get('type', ''),
                        'Capacity': unit.get('maxOccupancy') or unit.get('capacity', 0)
                    }
                    converted.append(converted_unit)
                    if i < 3:
                        logger.info(f"Successfully converted unit {i}: {converted_unit}")
                else:
                    if i < 10:
                        logger.warning(f"Skipping unit {i} - missing unit code: {unit}")
                        
            except Exception as e:
                if i < 10:
                    logger.error(f"Error converting unit {i}: {e}")
                continue
        
        logger.info(f"Unit conversion complete: {len(converted)} out of {len(units)} units converted")
        return converted
    
    def _is_reservation_fixed(self, reservation: Dict) -> bool:
        """Determine if a reservation is fixed (cannot be moved)"""
        # A reservation is fixed if:
        # 1. It's checked in or checked out
        # 2. It's explicitly marked as fixed in RMS
        # 3. It starts within 3 days
        
        # Check if explicitly marked as fixed
        if reservation.get('fixedRes', False):
            return True
        
        status = reservation.get('status', '').lower()
        if status in ['checkedin', 'checkedout']:
            return True
        
        arrival_date = reservation.get('arrivalDate', '')
        if arrival_date:
            try:
                arrive_date = datetime.strptime(arrival_date[:10], '%Y-%m-%d').date()
                if arrive_date <= datetime.now().date() + timedelta(days=3):
                    return True
            except:
                pass
        
        return False
    
    def _calculate_occupancy_matrix(self, reservations_data: List[Dict], inventory_data: List[Dict],
                                  constraint_start_date, constraint_end_date) -> Tuple[Dict, set, Dict]:
        """Calculate occupancy matrix showing unit availability"""
        logger.info("Building occupancy matrix...")
        
        # Group units by category using actual category names from reservations
        # First, build a mapping from categoryId to categoryName
        category_id_to_name = {}
        for res in reservations_data:
            category_name = res.get('category', '')
            # Extract categoryId from unit['Category'] if it's in format 'Category_XXXX'
            for unit in inventory_data:
                unit_category = unit.get('Category', '')
                if unit_category.startswith('Category_'):
                    category_id = unit_category.replace('Category_', '')
                    # This is a rough mapping - we'll use the reservation category names instead
                    pass
        
        # Group units by the actual category names from reservations
        units_by_category = defaultdict(list)
        category_name_mapping = {}
        
        # Build mapping from unit area names to category names using reservations
        for res in reservations_data:
            unit_area = res.get('Unit/Site', '')
            category_name = res.get('category', '')
            if unit_area and category_name:
                category_name_mapping[unit_area] = category_name
        
        # Now group units by actual category names
        for unit in inventory_data:
            unit_code = unit['Unit/Site']
            if unit_code:
                # Use the category name from reservations if available
                category = category_name_mapping.get(unit_code, unit['Category'])
                units_by_category[category].append(unit_code)
        
        logger.info(f"Units by category: {dict(units_by_category)}")
        
        # Generate date range
        dates = set()
        current = constraint_start_date
        while current <= constraint_end_date:
            dates.add(current)
            current += timedelta(days=1)
        
        logger.info(f"Date range: {len(dates)} days from {min(dates)} to {max(dates)}")
        
        # Build occupancy matrix
        occupancy = {}
        
        for res in reservations_data:
            try:
                arrive_date = datetime.strptime(res['Arrive'], '%Y-%m-%d').date()
                depart_date = datetime.strptime(res['Depart'], '%Y-%m-%d').date()
                unit = res['Unit/Site']
                
                if arrive_date and depart_date and unit:
                    # Clip to constraint period
                    effective_arrive = max(arrive_date, constraint_start_date)
                    effective_depart = min(depart_date, constraint_end_date + timedelta(days=1))
                    
                    # Mark occupied dates
                    current_date = effective_arrive
                    while current_date < effective_depart:
                        if current_date in dates:
                            occupancy[(unit, current_date)] = {
                                'reservation_id': res.get('reservationId', ''),
                                'guest_name': f"{res['firstName']} {res['lastName']}",
                                'is_fixed': res['is_fixed']
                            }
                        current_date += timedelta(days=1)
            except Exception as e:
                logger.warning(f"Error processing reservation for occupancy: {e}")
                continue
        
        logger.info(f"Occupancy matrix built: {len(occupancy)} occupied unit-days")
        return occupancy, dates, dict(units_by_category)
    
    def _calculate_category_strategic_importance(self, reservations_data: List[Dict], 
                                               inventory_data: List[Dict],
                                               constraint_start_date, constraint_end_date,
                                               occupancy: Dict, dates: set, 
                                               units_by_category: Dict) -> Dict[str, float]:
        """Calculate strategic importance score for each category"""
        logger.info("Calculating strategic importance for categories...")
        
        category_importance = {}
        
        for category, units in units_by_category.items():
            if len(units) <= 1:
                category_importance[category] = 0.0
                logger.debug(f"Category {category}: 0.0 (only {len(units)} unit)")
                continue
            
            # Calculate contiguous availability patterns
            total_contiguous_score = 0
            total_dates = len(dates)
            
            for date in dates:
                available_units = 0
                for unit in units:
                    if (unit, date) not in occupancy:
                        available_units += 1
                
                # Score based on contiguous availability
                if available_units >= 3:
                    total_contiguous_score += available_units * available_units
            
            # Strategic importance based on fragmentation potential
            if total_dates > 0:
                avg_contiguous_score = total_contiguous_score / total_dates
                strategic_importance = min(1.0, avg_contiguous_score / 100.0)
            else:
                strategic_importance = 0.0
            
            category_importance[category] = strategic_importance
            logger.info(f"Category {category}: {strategic_importance:.3f}")
        
        return category_importance
    
    def _suggest_moves(self, reservations_data: List[Dict], inventory_data: List[Dict],
                      occupancy: Dict, dates: set, units_by_category: Dict,
                      category_importance: Dict, constraint_start_date, constraint_end_date) -> List[Dict]:
        """Find optimal move suggestions using fragmentation analysis"""
        logger.info("Finding move suggestions...")
        
        suggestions = []
        applied_moves = {}
        
        # Process each category
        for category, units in units_by_category.items():
            if len(units) <= 1:
                continue
            
            strategic_importance = category_importance.get(category, 0.0)
            if strategic_importance == 0.0:
                logger.debug(f"Skipping category {category} - no strategic importance")
                continue
            
            logger.info(f"Analyzing category {category} with {len(units)} units")
            
            # Get moveable reservations in this category
            moveable_reservations = self._get_moveable_reservations(
                reservations_data, category, applied_moves, constraint_start_date, constraint_end_date
            )
            
            if not moveable_reservations:
                logger.debug(f"No moveable reservations in category {category}")
                continue
            
            # Calculate current fragmentation score
            current_occupancy = self._apply_moves_to_occupancy(occupancy, applied_moves)
            current_score = self._calculate_fragmentation_score(category, units, dates, current_occupancy)
            
            # Find best moves for this category
            category_suggestions = self._find_best_moves_for_category(
                moveable_reservations, units, dates, current_occupancy, current_score,
                category, strategic_importance, constraint_end_date
            )
            
            suggestions.extend(category_suggestions)
            
            # Apply the moves for future iterations
            for suggestion in category_suggestions:
                move_key = f"{suggestion['reservation_id']}_{suggestion['from_unit']}"
                applied_moves[move_key] = suggestion['to_unit']
        
        logger.info(f"Found {len(suggestions)} total move suggestions")
        return suggestions
    
    def _get_moveable_reservations(self, reservations_data: List[Dict], category: str,
                                 applied_moves: Dict, constraint_start_date, constraint_end_date) -> List[Dict]:
        """Get reservations that can be moved within a category"""
        moveable = []
        
        for res in reservations_data:
            if res.get('category') == category and not res.get('is_fixed', False):
                # Check if not already moved
                move_key = f"{res.get('reservationId', '')}_{res.get('Unit/Site', '')}"
                if move_key not in applied_moves:
                    
                    # Check if within analysis period
                    try:
                        arrive_date = datetime.strptime(res['Arrive'], '%Y-%m-%d').date()
                        depart_date = datetime.strptime(res['Depart'], '%Y-%m-%d').date()
                        
                        if (arrive_date >= constraint_start_date and 
                            depart_date <= constraint_end_date + timedelta(days=1)):
                            moveable.append(res)
                    except:
                        continue
        
        return moveable
    
    def _apply_moves_to_occupancy(self, occupancy: Dict, applied_moves: Dict) -> Dict:
        """Apply previously made moves to occupancy matrix"""
        # For now, return original occupancy
        # In full implementation, this would simulate move effects
        return occupancy.copy()
    
    def _calculate_fragmentation_score(self, category: str, units: List[str], 
                                     dates: set, occupancy: Dict) -> float:
        """Calculate fragmentation score for category - lower is better"""
        total_gaps = 0
        total_available_days = 0
        strategic_value = 0
        
        for unit in units:
            available_periods = self._find_contiguous_availability(unit, dates, occupancy)
            for start, end, days in available_periods:
                total_available_days += days
                if days > 0:
                    total_gaps += 1
                    # Strategic value: longer contiguous periods are exponentially more valuable
                    strategic_value += days * days
        
        if total_gaps == 0:
            return 0
        
        # Lower score = better (less fragmented)
        fragmentation_penalty = total_gaps * 10
        strategic_bonus = strategic_value / 100
        
        return fragmentation_penalty - strategic_bonus
    
    def _find_contiguous_availability(self, unit: str, dates: set, occupancy: Dict) -> List[Tuple]:
        """Find contiguous available periods for a unit"""
        available_periods = []
        current_start = None
        
        for date in sorted(dates):
            if (unit, date) not in occupancy:
                if current_start is None:
                    current_start = date
            else:
                if current_start is not None:
                    days = (date - current_start).days
                    available_periods.append((current_start, date, days))
                    current_start = None
        
        # Handle period extending to end
        if current_start is not None:
            end_date = max(dates) + timedelta(days=1)
            days = (end_date - current_start).days
            available_periods.append((current_start, end_date, days))
        
        return available_periods
    
    def _find_best_moves_for_category(self, moveable_reservations: List[Dict], units: List[str],
                                    dates: set, current_occupancy: Dict, current_score: float,
                                    category: str, strategic_importance: float,
                                    constraint_end_date) -> List[Dict]:
        """Find the best moves for a specific category"""
        category_suggestions = []
        max_moves_per_category = 3  # Limit to prevent too many suggestions
        
        for res in moveable_reservations[:10]:  # Limit reservations to analyze
            current_unit = res.get('Unit/Site', '')
            
            # Try moving to each other unit in category
            for target_unit in units:
                if target_unit == current_unit:
                    continue
                
                # Check if move is possible
                if self._can_move_reservation(res, target_unit, dates, current_occupancy, constraint_end_date):
                    # Calculate improvement
                    temp_occupancy = self._simulate_move(current_occupancy, res, target_unit, constraint_end_date)
                    new_score = self._calculate_fragmentation_score(category, units, dates, temp_occupancy)
                    
                    improvement = current_score - new_score  # Positive is better
                    
                    if improvement > 0.1:  # Minimum improvement threshold
                        suggestion = {
                            'reservation_id': res.get('reservationId', ''),
                            'guest_name': f"{res.get('firstName', '')} {res.get('lastName', '')}".strip(),
                            'from_unit': current_unit,
                            'to_unit': target_unit,
                            'check_in': res.get('Arrive', ''),
                            'check_out': res.get('Depart', ''),
                            'category': category,
                            'improvement_score': improvement,
                            'strategic_importance': strategic_importance,
                            'reason': f"Defragmentation move to improve {category} availability"
                        }
                        category_suggestions.append(suggestion)
                        
                        if len(category_suggestions) >= max_moves_per_category:
                            break
            
            if len(category_suggestions) >= max_moves_per_category:
                break
        
        # Sort by improvement and return best ones
        category_suggestions.sort(key=lambda x: x['improvement_score'], reverse=True)
        return category_suggestions[:max_moves_per_category]
    
    def _can_move_reservation(self, reservation: Dict, target_unit: str, dates: set,
                            occupancy: Dict, constraint_end_date) -> bool:
        """Check if a reservation can be moved to target unit"""
        try:
            arrive_date = datetime.strptime(reservation['Arrive'], '%Y-%m-%d').date()
            depart_date = datetime.strptime(reservation['Depart'], '%Y-%m-%d').date()
            
            # Check availability for all nights
            current_date = arrive_date
            while current_date < depart_date:
                if current_date in dates and (target_unit, current_date) in occupancy:
                    return False  # Conflict found
                current_date += timedelta(days=1)
            
            return True
        except:
            return False
    
    def _simulate_move(self, occupancy: Dict, reservation: Dict, target_unit: str,
                      constraint_end_date) -> Dict:
        """Simulate moving a reservation to a new unit"""
        temp_occupancy = occupancy.copy()
        
        try:
            arrive_date = datetime.strptime(reservation['Arrive'], '%Y-%m-%d').date()
            depart_date = datetime.strptime(reservation['Depart'], '%Y-%m-%d').date()
            current_unit = reservation.get('Unit/Site', '')
            
            # Remove from current unit
            current_date = arrive_date
            while current_date < depart_date:
                if (current_unit, current_date) in temp_occupancy:
                    del temp_occupancy[(current_unit, current_date)]
                current_date += timedelta(days=1)
            
            # Add to target unit
            current_date = arrive_date
            while current_date < depart_date:
                temp_occupancy[(target_unit, current_date)] = {
                    'reservation_id': reservation.get('reservationId', ''),
                    'guest_name': f"{reservation.get('firstName', '')} {reservation.get('lastName', '')}",
                    'is_fixed': reservation.get('is_fixed', False)
                }
                current_date += timedelta(days=1)
        except:
            pass
        
        return temp_occupancy
