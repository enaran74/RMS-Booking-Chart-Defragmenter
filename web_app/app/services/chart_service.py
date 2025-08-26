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
from utils import get_logger


class BookingChartService:
    def __init__(self):
        """Initialize the booking chart service"""
        self.logger = get_logger()
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
            
            # Get fresh RMS data (ALL reservations - like CLI does)
            rms_property_id = self.defrag_service._get_rms_property_id(property_obj)
            rms_client = self.defrag_service.rms_client
            
            # Fetch fresh RMS data (use standard date range)
            reservations_data = rms_client.get_property_reservations(rms_property_id)
            inventory_data = rms_client.get_property_units(rms_property_id)
            
            if not reservations_data or not inventory_data:
                self.logger.warning(f"No RMS data available for property {property_code}")
                return None
            
            # Convert to DataFrame format (same as CLI)
            reservations_df = rms_client._convert_to_original_dataframe_format(reservations_data, 'reservations', rms_property_id)
            inventory_df = rms_client._convert_to_original_dataframe_format(inventory_data, 'units', rms_property_id)
            
            self.logger.info(f"Fresh RMS data: {len(reservations_df)} reservations, {len(inventory_df)} units")
            
            # DEBUG: Log all guest names we received from RMS
            target_guests = ['Coombs', 'JIANMIN', 'Trembath', 'Anderson', 'Murray', 'Peterson', 'Brown']
            self.logger.info(f"🔍 DEBUG: Looking for specific guests in RMS data: {target_guests}")
            
            found_guests = {}
            for _, res in reservations_df.iterrows():
                guest_name = res.get('Surname', '').strip()
                if guest_name in target_guests:
                    if guest_name not in found_guests:
                        found_guests[guest_name] = []
                    found_guests[guest_name].append({
                        'res_no': res.get('Res No'),
                        'arrive': res.get('Arrive'),
                        'depart': res.get('Depart'),
                        'unit': res.get('Unit/Site'),
                        'status': res.get('Status')
                    })
            
            self.logger.info(f"🔍 DEBUG: Found guests in RMS data: {list(found_guests.keys())}")
            for guest, reservations_list in found_guests.items():
                for res in reservations_list:
                    self.logger.info(f"  {guest}: Res#{res['res_no']} | {res['arrive']} → {res['depart']} | {res['unit']} | {res['status']}")
            
            if not found_guests:
                self.logger.warning(f"🔍 DEBUG: None of the target guests found in RMS response!")
                self.logger.info(f"🔍 DEBUG: Sample guests from RMS (first 10):")
                for i, (_, res) in enumerate(reservations_df.head(10).iterrows()):
                    self.logger.info(f"  {i+1}. {res.get('Surname', 'Unknown')} | Res#{res.get('Res No')} | {res.get('Arrive')} → {res.get('Depart')} | {res.get('Unit/Site')}")
            
            self.logger.info(f"🔍 DEBUG: Total reservations returned from RMS API: {len(reservations_data)} raw, {len(reservations_df)} after conversion")
            
            # Get move suggestions for highlighting only
            latest_analysis = db.query(DefragMove).filter(
                DefragMove.property_code == property_code.upper()
            ).order_by(DefragMove.analysis_date.desc()).first()
            
            suggestions = []
            if latest_analysis and latest_analysis.move_data:
                suggestions = latest_analysis.move_data.get('moves', [])
            
            # Set time constraints for chart display (start from today in AEST)
            # Container is UTC, so add 10 hours to get AEST, then take just the date part
            now_utc = datetime.now()
            now_aest = now_utc + timedelta(hours=10)
            today_aest_date = now_aest.date()
            
            # Chart should start from AEST today at midnight (as UTC datetime)
            constraint_start_date = datetime.combine(today_aest_date, datetime.min.time())
            constraint_end_date = constraint_start_date + timedelta(days=30)
            
            self.logger.info(f"📅 AEST Date calculation: UTC={now_utc.date()}, AEST={today_aest_date}")
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
        
        for suggestion in suggestions:
            # Get current unit from the reservation (same as CLI)
            res_no = suggestion.get('reservation_id')  # Web format uses 'reservation_id'
            if res_no:
                res_row = reservations_df[reservations_df['Res No'] == res_no]
                current_unit = res_row.iloc[0]['Unit/Site'] if not res_row.empty else None
                
                suggestions_lookup[res_no] = {
                    'order': suggestion.get('sequential_order'),
                    'target_unit': suggestion.get('to_unit'),  # Use 'to_unit' from move suggestions
                    'current_unit': suggestion.get('from_unit'),  # Use 'from_unit' from move suggestions
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

    def _get_status_color_class(self, status: str) -> str:
        """Get CSS color class for booking status (matching CLI Excel colors)"""
        if not status:
            return 'status-confirmed'
        
        status_lower = status.lower()
        if status_lower == 'arrived':
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
