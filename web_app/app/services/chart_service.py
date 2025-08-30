"""
Booking Chart Service - Following CLI ExcelGenerator approach
Generates booking chart data for the web UI by:
1. Building occupancy matrix from ALL RMS reservations
2. Using move suggestions ONLY for highlighting (styling)
"""

import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Any
from app.core.database import get_db
from app.services.defrag_service import DefragService
import logging


class BookingChartService:
    def __init__(self):
        """Initialize the booking chart service"""
        self.logger = logging.getLogger(__name__)
        self.defrag_service = DefragService()
        self.logger.info("BookingChartService initialized")

    async def get_chart_data_for_property(self, property_code: str) -> Dict[str, Any]:
        """Get booking chart data for a specific property following CLI approach"""
        try:
            self.logger.info(f"Getting chart data for property {property_code} using CLI approach")
            
            # Get property info from database (ensure session is closed to avoid pool exhaustion)
            from app.core.database import SessionLocal
            from app.models.property import Property
            from app.models.defrag_move import DefragMove
            db = SessionLocal()
            
            property_obj = db.query(Property).filter(Property.property_code == property_code.upper()).first()
            if not property_obj:
                self.logger.warning(f"Property {property_code} not found in database")
                return None
            
            # Get move suggestions for highlighting only
            latest_analysis = db.query(DefragMove).filter(
                DefragMove.property_code == property_code.upper()
            ).order_by(DefragMove.analysis_date.desc()).first()
            
            suggestions = []
            if latest_analysis and latest_analysis.move_data:
                suggestions = latest_analysis.move_data.get('moves', [])
            
            # Calculate chart date range - extend for holiday periods if holiday moves exist
            constraint_start_date, constraint_end_date = self._calculate_chart_date_range(suggestions, property_obj)
            
            # Get fresh RMS data (ALL reservations - like CLI does)
            rms_property_id = self.defrag_service._get_rms_property_id(property_obj)
            rms_client = self.defrag_service.rms_client
            
            # Temporarily override RMS client date constraints for extended chart range
            original_start = rms_client.constraint_start_date
            original_end = rms_client.constraint_end_date
            
            # Set extended dates for chart data fetching
            rms_client.constraint_start_date = constraint_start_date.date()
            rms_client.constraint_end_date = constraint_end_date.date()
            
            try:
                # Fetch fresh RMS data with extended date range
                reservations_data = rms_client.get_property_reservations(rms_property_id)
                inventory_data = rms_client.get_property_units(rms_property_id)
            finally:
                # Always restore original constraint dates
                rms_client.constraint_start_date = original_start
                rms_client.constraint_end_date = original_end
            
            if not reservations_data or not inventory_data:
                self.logger.warning(f"No RMS data available for property {property_code}")
                return None
            
            # Convert to DataFrame format (same as CLI)
            reservations_df = rms_client._convert_to_original_dataframe_format(reservations_data, 'reservations', rms_property_id)
            inventory_df = rms_client._convert_to_original_dataframe_format(inventory_data, 'units', rms_property_id)
            
            self.logger.info(f"Fresh RMS data: {len(reservations_df)} reservations, {len(inventory_df)} units")
            
            self.logger.info(f"📅 Chart date range: {constraint_start_date.date()} to {constraint_end_date.date()}")
            
            # Generate chart data using CLI approach
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
        finally:
            try:
                db.close()
            except Exception:
                pass

    def generate_chart_data(self, property_code: str, reservations_df: pd.DataFrame,
                          inventory_df: pd.DataFrame, suggestions: List[Dict],
                          constraint_start_date: datetime, constraint_end_date: datetime) -> Dict[str, Any]:
        """Generate chart data following CLI ExcelGenerator approach"""
        try:
            self.logger.info(f"Generating chart data for property {property_code} (CLI approach)")

            # Normalize category strings in both dataframes to avoid grouping mismatches
            def normalize_category(value: str) -> str:
                if pd.isna(value):
                    return ''
                s = str(value)
                s = s.replace('–', '-').replace('—', '-')
                s = ' '.join(s.split())
                return s.strip()

            # Normalize unit/site strings (collapse multiple spaces)
            def normalize_unit(value: str) -> str:
                if pd.isna(value):
                    return ''
                return ' '.join(str(value).split()).strip()

            if 'Category' in reservations_df.columns:
                reservations_df['Category'] = reservations_df['Category'].apply(normalize_category)
            if 'Category' in inventory_df.columns:
                inventory_df['Category'] = inventory_df['Category'].apply(normalize_category)
            # Normalize unit/site strings on reservations as well so all downstream lookups match
            if 'Unit/Site' in reservations_df.columns:
                reservations_df['Unit/Site'] = reservations_df['Unit/Site'].apply(normalize_unit)
            
            # Generate date range (same as CLI)
            date_range = []
            current_date = constraint_start_date
            while current_date <= constraint_end_date:
                date_range.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)
            
            self.logger.info(f"Generated date range: {date_range[:5]}...{date_range[-3:]} (total: {len(date_range)} days)")
            
            # Build suggestions lookup (same as CLI - lines 102-114 in excel_generator.py)
            suggestions_lookup = self._build_suggestions_lookup(suggestions, reservations_df)
            
            # Group units by category (same as CLI)
            # Apply unit-normalization to inventory before grouping
            if 'Unit/Site' in inventory_df.columns:
                inventory_df['Unit/Site'] = inventory_df['Unit/Site'].apply(normalize_unit)
            units_by_category = self._group_units_by_category(inventory_df)

            # Debug: compare category sets between reservations and inventory
            inv_cats = set(units_by_category.keys())
            res_cats = set(reservations_df['Category'].unique().tolist()) if 'Category' in reservations_df.columns else set()
            self.logger.info(f"🔎 Category comparison: inventory={len(inv_cats)} reservations={len(res_cats)}")
            self.logger.info(f"Some inventory categories: {list(sorted(inv_cats))[:6]}")
            self.logger.info(f"Some reservation categories: {list(sorted(res_cats))[:6]}")
            
            # Build occupancy matrix from ALL RMS reservations (same as CLI - lines 314-336)
            occupancy = self._build_occupancy_matrix(reservations_df, constraint_start_date, constraint_end_date)

            # Targeted debug for CALI-104 and date 2025-09-03
            debug_unit = 'CALI-104 D2B 1Q2B'
            debug_date = '2025-09-03'
            if debug_unit in occupancy and debug_date in occupancy.get(debug_unit, {}):
                b = occupancy[debug_unit][debug_date]
                self.logger.info(f"✅ DEBUG OCCUPANCY: {debug_unit} on {debug_date}: res={b.get('res_no')} guest={b.get('surname')} status={b.get('status')}")
            else:
                self.logger.info(f"⚠️ DEBUG OCCUPANCY: {debug_unit} on {debug_date} is EMPTY in occupancy matrix")

            # Targeted debug: list all reservations covering 2025-09-03 for 103/104/108/109
            try:
                target_date = datetime(2025, 9, 3)
                units_interest = {
                    'CALI-103 D2B 1Q2B', 'CALI-104 D2B 1Q2B', 'CALI-108 D2B 1Q2B', 'CALI-109 D2B 1Q2B'
                }
                self.logger.info("🔎 DEBUG TARGET DATE 2025-09-03 - reservations covering date for 103/104/108/109:")
                for _, r in reservations_df.iterrows():
                    unit_name = ' '.join(str(r.get('Unit/Site', '')).split())
                    if unit_name not in units_interest:
                        continue
                    a = self._parse_date(r.get('Arrive', ''))
                    d = self._parse_date(r.get('Depart', ''))
                    if not a or not d:
                        continue
                    if a <= target_date < d:
                        self.logger.info(f"   • {unit_name}: {r.get('Surname')} Res#{r.get('Res No')} {a.date()}→{d.date()} ({r.get('Status')})")
            except Exception as _e:
                pass
            
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
                    
                    # Add ghost bookings for move suggestions targeting this unit
                    ghost_bookings = self._create_ghost_bookings(unit, date_range, suggestions_lookup, occupancy)
                    booking_spans.extend(ghost_bookings)
                    
                    unit_data["bookings"] = booking_spans
                    
                    category_data["units"].append(unit_data)
                
                chart_data["categories"].append(category_data)
            
            self.logger.info(f"Chart data generated successfully: {len(chart_data['categories'])} categories")
            return chart_data
            
        except Exception as e:
            self.logger.error(f"Error generating chart data for {property_code}: {str(e)}")
            raise

    def _build_suggestions_lookup(self, suggestions: List[Dict], reservations_df: pd.DataFrame) -> Dict[str, Dict]:
        """Build lookup table for move suggestions (same as CLI - lines 102-114)"""
        suggestions_lookup = {}
        
        self.logger.info(f"Building suggestions lookup from {len(suggestions)} suggestions")
        
        for idx, suggestion in enumerate(suggestions):
            # Get current unit from the reservation (same as CLI)
            res_no = suggestion.get('reservation_id')  # Web format uses 'reservation_id'
            if res_no:
                res_row = reservations_df[reservations_df['Res No'] == res_no]
                current_unit = res_row.iloc[0]['Unit/Site'] if not res_row.empty else None
                
                target_unit = suggestion.get('to_unit', '')
                current_unit_from_suggestion = suggestion.get('from_unit', '')
                
                self.logger.info(f"🔍 Suggestion {idx}: res#{res_no} from '{current_unit_from_suggestion}' to '{target_unit}'")
                
                suggestions_lookup[res_no] = {
                    'order': suggestion.get('sequential_order'),
                    'target_unit': target_unit,  # Use 'target_unit' from move suggestions
                    'current_unit': current_unit_from_suggestion,  # Use 'current_unit' from move suggestions
                    'score': suggestion.get('score', 0),
                    'is_move_suggestion': True
                }
        
        self.logger.info(f"Built suggestions lookup with {len(suggestions_lookup)} entries")
        return suggestions_lookup

    def _group_units_by_category(self, inventory_df: pd.DataFrame) -> Dict[str, List[str]]:
        """Group units by accommodation category (same as CLI)"""
        units_by_category = defaultdict(list)
        
        self.logger.info(f"Processing inventory data with {len(inventory_df)} units")
        
        for _, unit in inventory_df.iterrows():
            category = unit.get('Category', 'Unknown')
            unit_code = unit.get('Unit/Site', '')
            if unit_code:
                units_by_category[category].append(unit_code)
        
        self.logger.info(f"Grouped units into {len(units_by_category)} categories: {list(units_by_category.keys())}")
        return dict(units_by_category)

    def _build_occupancy_matrix(self, reservations_df: pd.DataFrame,
                               start_date: datetime, end_date: datetime) -> Dict[str, Dict[str, Dict]]:
        """Build occupancy matrix from ALL RMS reservations (same as CLI - lines 314-336)"""
        occupancy = {}  # Use regular dict like CLI
        
        self.logger.info(f"Building occupancy matrix from {len(reservations_df)} RMS reservations")
        
        for _, res in reservations_df.iterrows():
            arrive_date = self._parse_date(res['Arrive'])
            depart_date = self._parse_date(res['Depart'])
            # Normalize unit code to match inventory naming
            unit = ' '.join(str(res['Unit/Site']).split()).strip()
            
            # Debug specific guests
            guest_name = res.get('Surname', '')
            if guest_name in ['Coombs', 'JIANMIN']:
                self.logger.info(f"Processing RMS reservation - Res {res['Res No']} ({guest_name}): Arrive='{res['Arrive']}' -> {arrive_date}, Depart='{res['Depart']}' -> {depart_date}")
                self.logger.info(f"  Unit: {unit}, Status: {res.get('Status')}")
            
            if arrive_date and depart_date:
                # Same logic as CLI (lines 322-336)
                current_date = max(arrive_date, start_date)
                end_occupancy = min(depart_date, end_date + timedelta(days=1))
                
                if guest_name in ['Coombs', 'JIANMIN']:
                    self.logger.info(f"  Building occupancy for {guest_name}: {current_date} to {end_occupancy}")
                
                while current_date < end_occupancy and current_date <= end_date:
                    # Key format: (unit, date) like CLI, but we'll use nested dict for web
                    date_key = current_date.strftime("%Y-%m-%d")
                    
                    if unit not in occupancy:
                        occupancy[unit] = {}
                    # Detect collisions where two bookings would occupy the same unit/date
                    if date_key in occupancy[unit]:
                        existing = occupancy[unit][date_key]
                        self.logger.warning(
                            f"🟠 OCCUPANCY CONFLICT {unit} {date_key}: existing res={existing.get('res_no')} guest={existing.get('surname')} "
                            f"vs new res={res['Res No']} guest={res['Surname']}"
                        )
                    occupancy[unit][date_key] = {
                        'res_no': res['Res No'],
                        'surname': res['Surname'],
                        'status': res['Status'],
                        'category': res['Category'],
                        'arrive': arrive_date,
                        'depart': depart_date,
                        'nights': res['Nights'],
                        'fixed': self._is_reservation_fixed(res)  # Use actual Fixed field from RMS API
                    }
                    
                    if guest_name in ['Coombs', 'JIANMIN']:
                        self.logger.info(f"  Added {guest_name} to {unit} on {date_key}")
                    
                    current_date += timedelta(days=1)
        
        total_entries = sum(len(dates) for dates in occupancy.values())
        self.logger.info(f"Built occupancy matrix with {total_entries} unit-date entries from ALL RMS reservations")
        return occupancy

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
                if current_span and current_span['reservation_no'] == booking['res_no']:
                    # Extend current span
                    current_span['end_date'] = date_str
                    current_span['nights'] += 1
                else:
                    # Start new span
                    if current_span:
                        spans.append(current_span)
                    
                    # Check if this reservation has a move suggestion
                    is_move_suggestion = booking['res_no'] in suggestions_lookup
                    suggestion_info = suggestions_lookup.get(booking['res_no'], {}) if is_move_suggestion else {}
                    
                    current_span = {
                        'start_date': date_str,
                        'end_date': date_str,
                        'reservation_no': booking['res_no'],
                        'guest_name': booking['surname'],
                        'status': booking['status'],
                        'nights': 1,
                        'is_fixed': booking['fixed'],
                        'is_move_suggestion': is_move_suggestion,
                        'suggestion_order': suggestion_info.get('order', ''),
                        'target_unit': suggestion_info.get('target_unit', ''),
                        'current_unit': suggestion_info.get('current_unit', ''),
                        'move_score': suggestion_info.get('score', 0),
                        'color_class': self._get_status_color_class(booking['status'])
                    }
            else:
                # Gap in bookings
                if current_span:
                    spans.append(current_span)
                    current_span = None
        
        # Add the last span
        if current_span:
            spans.append(current_span)
        
        return spans

    def _create_ghost_bookings(self, target_unit: str, date_range: List[str], 
                             suggestions_lookup: Dict[str, Dict], occupancy: Dict[str, Dict]) -> List[Dict]:
        """Create ghost bookings for move suggestions targeting this unit"""
        ghost_bookings = []
        
        # Debug: Log what we're looking for
        self.logger.info(f"🔍 Creating ghost bookings for target unit: {target_unit}")
        self.logger.info(f"🔍 Available suggestions: {len(suggestions_lookup)} total")
        
        # Find all move suggestions that target this unit
        for reservation_no, suggestion_info in suggestions_lookup.items():
            suggestion_target = suggestion_info.get('target_unit', '')
            
            # Normalize both unit names for comparison (remove extra spaces)
            normalized_suggestion_target = ' '.join(suggestion_target.split())
            normalized_target_unit = ' '.join(target_unit.split())
            
            self.logger.info(f"🔍 Checking suggestion res#{reservation_no}: target='{suggestion_target}' (normalized: '{normalized_suggestion_target}') vs unit='{target_unit}' (normalized: '{normalized_target_unit}')")
            
            if normalized_suggestion_target == normalized_target_unit:
                self.logger.info(f"✅ Found matching suggestion for {target_unit}: res#{reservation_no}")
                # Find the original booking to get dates and guest name
                original_booking = self._find_booking_by_reservation(reservation_no, occupancy)
                if original_booking:
                    self.logger.info(f"✅ Found original booking for res#{reservation_no}: {original_booking['guest_name']}")
                    # Create ghost booking with same dates as original
                    ghost_booking = {
                        'start_date': original_booking['start_date'],
                        'end_date': original_booking['end_date'],
                        'reservation_no': f"GHOST-{reservation_no}",  # Unique identifier
                        'guest_name': original_booking['guest_name'],
                        'status': 'Ghost',  # Special status for ghost bookings
                        'nights': original_booking['nights'],
                        'is_fixed': False,
                        'is_move_suggestion': False,  # Not a move suggestion itself
                        'is_ghost_booking': True,  # New flag for ghost bookings
                        'original_reservation_no': reservation_no,  # Reference to original
                        'target_unit': target_unit,
                        'current_unit': suggestion_info.get('current_unit', ''),
                        'suggestion_order': suggestion_info.get('order', ''),
                        'move_score': suggestion_info.get('score', 0),
                        'color_class': 'status-ghost'  # Special CSS class for ghost styling
                    }
                    ghost_bookings.append(ghost_booking)
                else:
                    self.logger.warning(f"⚠️ Could not find original booking for res#{reservation_no}")
        
        self.logger.info(f"🔍 Created {len(ghost_bookings)} ghost bookings for {target_unit}")
        return ghost_bookings

    def _find_booking_by_reservation(self, reservation_no: str, occupancy: Dict[str, Dict]) -> Dict:
        """Find booking details by reservation number across all units"""
        for unit_code, unit_bookings in occupancy.items():
            for date_str, booking in unit_bookings.items():
                if booking.get('res_no') == reservation_no:
                    # Found the booking, now calculate its span
                    start_date = date_str
                    end_date = date_str
                    nights = 1
                    
                    # Find consecutive nights for the same reservation
                    date_keys = sorted([d for d, b in unit_bookings.items() if b.get('res_no') == reservation_no])
                    if date_keys:
                        start_date = date_keys[0]
                        end_date = date_keys[-1]
                        nights = len(date_keys)
                    
                    return {
                        'start_date': start_date,
                        'end_date': end_date,
                        'guest_name': booking.get('surname', ''),
                        'status': booking.get('status', ''),
                        'nights': nights,
                        'is_fixed': booking.get('fixed', False)
                    }
        return None

    def _get_status_color_class(self, status: str) -> str:
        """Get CSS color class for booking status (matching CLI Excel colors)"""
        if not status:
            return 'status-confirmed'
        
        status_lower = status.lower()
        if status_lower == 'ghost':
            return 'status-ghost'
        elif status_lower == 'arrived':
            return 'status-arrived'
        elif status_lower == 'confirmed':
            return 'status-confirmed'
        elif status_lower in ['unconfirmed', 'pending']:
            return 'status-unconfirmed'
        elif status_lower == 'maintenance':
            return 'status-maintenance'
        elif status_lower in ['pencil', 'tentative']:
            return 'status-pencil'
        else:
            return 'status-confirmed'  # Default to confirmed

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string (same logic as CLI)"""
        if not date_str or pd.isna(date_str):
            return None
        try:
            # Try DD/MM/YYYY HH:MM format first
            return datetime.strptime(date_str.split()[0], '%d/%m/%Y')
        except:
            try:
                return datetime.strptime(date_str, '%d/%m/%Y')
            except:
                try:
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    pass
                self.logger.warning(f"Could not parse date: {date_str}")
                return None
    
    def _is_reservation_fixed(self, reservation_row) -> bool:
        """Check if reservation is marked as fixed (same as CLI implementation)"""
        if 'Fixed' in reservation_row:
            fixed_value = reservation_row['Fixed']
            if isinstance(fixed_value, bool):
                return fixed_value
            elif isinstance(fixed_value, str):
                return fixed_value.lower() in ['true', '1', 'yes']
        return False
    
    def _calculate_chart_date_range(self, suggestions: List[Dict], property_obj) -> tuple:
        """Calculate chart date range, extending for holiday periods if holiday moves exist"""
        # Default date range (31 days from today in AEST)
        now_utc = datetime.now()
        now_aest = now_utc + timedelta(hours=10)
        today_aest_date = now_aest.date()
        
        default_start = datetime.combine(today_aest_date, datetime.min.time())
        default_end = default_start + timedelta(days=30)
        
        # Check if we have holiday moves
        holiday_moves = [s for s in suggestions if s.get('is_holiday_move', False)]
        
        if not holiday_moves or not property_obj.state_code:
            self.logger.info(f"📅 Using default 31-day chart range: no holiday moves or state code")
            return default_start, default_end
        
        self.logger.info(f"📅 Found {len(holiday_moves)} holiday moves, calculating extended range for {property_obj.state_code}")
        
        try:
            # Get holiday periods that generated moves
            from app.services.holiday_client import HolidayClient
            from datetime import date
            
            holiday_client = HolidayClient()
            holiday_periods = holiday_client.get_combined_holiday_periods_2month_forward(
                property_obj.state_code, 
                date.today()
            )
            
            if not holiday_periods:
                self.logger.info(f"📅 No holiday periods found, using default range")
                return default_start, default_end
            
            # Find the earliest and latest dates from holiday periods that generated moves
            # We only extend for periods that actually generated moves
            holiday_period_names = set(move.get('holiday_period') for move in holiday_moves if move.get('holiday_period'))
            relevant_periods = [p for p in holiday_periods if p['name'] in holiday_period_names]
            
            if not relevant_periods:
                self.logger.info(f"📅 No relevant holiday periods found, using default range")
                return default_start, default_end
            
            # Calculate extended range based on relevant holiday periods
            earliest_start = min(period['extended_start'] for period in relevant_periods)
            latest_end = max(period['extended_end'] for period in relevant_periods)
            
            # Convert to datetime objects
            extended_start = datetime.combine(earliest_start, datetime.min.time())
            extended_end = datetime.combine(latest_end, datetime.min.time())
            
            # Ensure we don't go backwards from today
            final_start = min(default_start, extended_start)
            final_end = max(default_end, extended_end)
            
            self.logger.info(f"📅 Extended chart range for holiday periods: {final_start.date()} to {final_end.date()}")
            self.logger.info(f"📅 Relevant holiday periods: {[p['name'] for p in relevant_periods]}")
            
            return final_start, final_end
            
        except Exception as e:
            self.logger.error(f"Error calculating extended chart range: {e}")
            self.logger.info(f"📅 Falling back to default range due to error")
            return default_start, default_end
