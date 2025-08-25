#!/usr/bin/env python3
"""
Booking Chart Service
Generates visual booking chart data for web interface
Extracted from ExcelGenerator logic for web compatibility
"""

import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Any
from app.core.database import get_db
from app.services.defrag_service import DefragService
from utils import get_logger


class BookingChartService:
    def __init__(self):
        """Initialize the booking chart service"""
        self.logger = get_logger()
        self.defrag_service = DefragService()
        self.logger.info("BookingChartService initialized")

    def generate_chart_data(self, property_code: str, reservations_df: pd.DataFrame, 
                          inventory_df: pd.DataFrame, suggestions: List[Dict],
                          constraint_start_date: datetime, constraint_end_date: datetime) -> Dict[str, Any]:
        """
        Generate booking chart data structure for web display
        
        Args:
            property_code: Property code (e.g., 'CALI')
            reservations_df: Reservation data
            inventory_df: Inventory/unit data
            suggestions: Move suggestions from defragmentation analysis
            constraint_start_date: Start date for chart
            constraint_end_date: End date for chart
            
        Returns:
            Dictionary containing structured chart data
        """
        try:
            self.logger.info(f"Generating chart data for property {property_code}")
            
            # Generate date range
            date_range = []
            current_date = constraint_start_date
            while current_date <= constraint_end_date:
                date_range.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)
            
            # Build suggestions lookup
            suggestions_lookup = self._build_suggestions_lookup(suggestions, reservations_df)
            
            # Group units by category
            units_by_category = self._group_units_by_category(inventory_df)
            
            # Build occupancy matrix
            occupancy = self._build_occupancy_matrix(reservations_df, constraint_start_date, constraint_end_date)
            
            # Generate chart structure
            chart_data = {
                "property_code": property_code,
                "date_range": date_range,
                "constraint_start_date": constraint_start_date.strftime("%Y-%m-%d"),
                "constraint_end_date": constraint_end_date.strftime("%Y-%m-%d"),
                "categories": []
            }
            
            # Process each category
            for category in sorted(units_by_category.keys()):
                units = sorted(units_by_category[category])
                category_data = {
                    "name": category,
                    "units": []
                }
                
                # Process each unit in category
                for unit in units:
                    unit_data = {
                        "unit_code": unit,
                        "bookings": []
                    }
                    
                    # Process bookings for this unit
                    unit_bookings = occupancy.get(unit, {})
                    
                    # Convert bookings to spans
                    booking_spans = self._create_booking_spans(unit_bookings, date_range, suggestions_lookup)
                    unit_data["bookings"] = booking_spans
                    
                    category_data["units"].append(unit_data)
                
                chart_data["categories"].append(category_data)
            
            self.logger.info(f"Chart data generated successfully: {len(chart_data['categories'])} categories")
            return chart_data
            
        except Exception as e:
            self.logger.error(f"Error generating chart data for {property_code}: {str(e)}")
            raise

    def _build_suggestions_lookup(self, suggestions: List[Dict], reservations_df: pd.DataFrame) -> Dict[str, Dict]:
        """Build lookup table for move suggestions"""
        suggestions_lookup = {}
        
        for suggestion in suggestions:
            res_no = suggestion.get('Reservation_No')
            if res_no:
                # Get current unit from the reservation
                res_row = reservations_df[reservations_df['Res No'] == res_no]
                current_unit = res_row.iloc[0]['Unit/Site'] if not res_row.empty else None
                
                suggestions_lookup[res_no] = {
                    'order': suggestion.get('Sequential_Order'),
                    'target_unit': suggestion.get('Suggested_Unit'),
                    'current_unit': current_unit,
                    'score': suggestion.get('Improvement_Score', 0),
                    'is_holiday_move': suggestion.get('is_holiday_move', False)
                }
        
        return suggestions_lookup

    def _group_units_by_category(self, inventory_df: pd.DataFrame) -> Dict[str, List[str]]:
        """Group units by accommodation category"""
        units_by_category = defaultdict(list)
        
        for _, unit in inventory_df.iterrows():
            category = unit.get('Category', 'Unknown')
            unit_code = unit.get('Unit/Site', '')
            if unit_code:
                units_by_category[category].append(unit_code)
        
        return dict(units_by_category)

    def _build_occupancy_matrix(self, reservations_df: pd.DataFrame, 
                               start_date: datetime, end_date: datetime) -> Dict[str, Dict[str, Dict]]:
        """Build occupancy matrix from reservations"""
        occupancy = defaultdict(dict)
        
        for _, res in reservations_df.iterrows():
            unit = res.get('Unit/Site')
            if not unit:
                continue
                
            # Parse dates
            arrive_date = self._parse_date(res.get('Arrive'))
            depart_date = self._parse_date(res.get('Depart'))
            
            if not arrive_date or not depart_date:
                continue
            
            # Create booking info
            booking_info = {
                'reservation_no': res.get('Res No'),
                'guest_name': res.get('Surname', ''),
                'status': res.get('Status', 'Confirmed'),
                'arrive_date': arrive_date,
                'depart_date': depart_date,
                'nights': (depart_date - arrive_date).days,
                'is_fixed': res.get('Status') in ['Arrived', 'Maintenance']  # Fixed bookings
            }
            
            # Add to occupancy matrix for each night
            current_date = max(arrive_date, start_date)
            end_occupancy = min(depart_date, end_date + timedelta(days=1))
            
            while current_date < end_occupancy and current_date <= end_date:
                date_key = current_date.strftime("%Y-%m-%d")
                occupancy[unit][date_key] = booking_info
                current_date += timedelta(days=1)
        
        return dict(occupancy)

    def _create_booking_spans(self, unit_bookings: Dict[str, Dict], 
                            date_range: List[str], suggestions_lookup: Dict[str, Dict]) -> List[Dict]:
        """Create booking spans from daily occupancy data"""
        spans = []
        
        if not unit_bookings:
            return spans
        
        # Group consecutive nights into spans
        current_span = None
        
        for date_str in date_range:
            booking = unit_bookings.get(date_str)
            
            if booking:
                if current_span and current_span['reservation_no'] == booking['reservation_no']:
                    # Extend current span
                    current_span['end_date'] = date_str
                    current_span['nights'] += 1
                else:
                    # Start new span
                    if current_span:
                        spans.append(current_span)
                    
                    # Check if this booking has move suggestions
                    res_no = booking['reservation_no']
                    is_move_suggestion = res_no in suggestions_lookup
                    move_info = suggestions_lookup.get(res_no, {})
                    
                    current_span = {
                        'reservation_no': res_no,
                        'guest_name': self._safe_surname(booking['guest_name'], booking['status']),
                        'status': booking['status'],
                        'start_date': date_str,
                        'end_date': date_str,
                        'nights': 1,
                        'is_fixed': booking['is_fixed'],
                        'is_move_suggestion': is_move_suggestion,
                        'move_info': move_info,
                        'color_class': self._get_status_color_class(booking['status'])
                    }
            else:
                # No booking - end current span if exists
                if current_span:
                    spans.append(current_span)
                    current_span = None
        
        # Add final span if exists
        if current_span:
            spans.append(current_span)
        
        return spans

    def _parse_date(self, date_value) -> Optional[datetime]:
        """Parse date from various formats"""
        if pd.isna(date_value):
            return None
        
        if isinstance(date_value, datetime):
            return date_value
        
        try:
            if isinstance(date_value, str):
                # Try common formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue
        except Exception:
            pass
        
        return None

    def _safe_surname(self, surname: str, status: str) -> str:
        """Create safe surname display (truncated, handles special characters)"""
        if not surname:
            return status.upper()[:4] if status else "UNKN"
        
        # Clean and truncate surname
        clean_surname = str(surname).strip()
        if len(clean_surname) > 8:
            clean_surname = clean_surname[:8]
        
        return clean_surname

    def _get_status_color_class(self, status: str) -> str:
        """Get CSS class for booking status color"""
        status_colors = {
            'Arrived': 'status-arrived',
            'Confirmed': 'status-confirmed', 
            'Unconfirmed': 'status-unconfirmed',
            'Maintenance': 'status-maintenance',
            'Pencil': 'status-pencil'
        }
        
        return status_colors.get(status, 'status-confirmed')

    async def get_chart_data_for_property(self, property_code: str) -> Dict[str, Any]:
        """
        Get chart data for a specific property by fetching fresh RMS data
        
        Args:
            property_code: Property code to get chart data for
            
        Returns:
            Chart data dictionary or None if no data available
        """
        try:
            self.logger.info(f"Fetching fresh RMS data for chart generation for property {property_code}")
            
            # Get property ID from property code
            from app.core.database import get_db
            from app.models.property import Property
            db = next(get_db())
            
            property_obj = db.query(Property).filter(Property.property_code == property_code.upper()).first()
            if not property_obj:
                self.logger.warning(f"Property {property_code} not found in database")
                return None
            
            # Get RMS property ID
            rms_property_id = self.defrag_service._get_rms_property_id(property_obj)
            
            # Get fresh data from RMS using the lightweight client
            rms_client = self.defrag_service.rms_client
            
            # Get reservation and inventory data
            reservations_data = rms_client.get_property_reservations(rms_property_id)
            inventory_data = rms_client.get_property_units(rms_property_id)
            
            if not reservations_data or not inventory_data:
                self.logger.warning(f"No RMS data available for property {property_code}")
                return None
            
            # Convert to pandas DataFrames (similar to excel_generator.py)
            import pandas as pd
            reservations_df = pd.DataFrame(reservations_data)
            inventory_df = pd.DataFrame(inventory_data)
            
            # Set date constraints (30 days from today)
            from datetime import datetime, timedelta
            constraint_start_date = datetime.now()
            constraint_end_date = constraint_start_date + timedelta(days=30)
            
            # Get stored move suggestions from database (reuse existing db session)
            from app.models.defrag_move import DefragMove
            
            latest_analysis = db.query(DefragMove).filter(
                DefragMove.property_code == property_code.upper()
            ).order_by(DefragMove.analysis_date.desc()).first()
            
            suggestions = []
            if latest_analysis and latest_analysis.move_data:
                suggestions = latest_analysis.move_data.get('moves', [])
            
            # Generate chart data
            chart_data = self.generate_chart_data(
                property_code=property_code,
                reservations_df=reservations_df,
                inventory_df=inventory_df,
                suggestions=suggestions,
                constraint_start_date=constraint_start_date,
                constraint_end_date=constraint_end_date
            )
            
            return chart_data
            
        except Exception as e:
            self.logger.error(f"Error getting chart data for property {property_code}: {str(e)}")
            return None
