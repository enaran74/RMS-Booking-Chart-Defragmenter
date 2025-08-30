#!/usr/bin/env python3
"""
School Holiday Client for RMS Booking Chart Defragmenter

Handles loading and processing of school holiday data from JSON file.
Integrates with the existing holiday system to provide combined holiday periods.
"""

import json
import os
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from app.services.utils import get_logger


class SchoolHolidayClient:
    """
    Client for handling school holiday data from JSON file
    """
    
    def __init__(self, json_file_path: str = "school_holidays.json"):
        """
        Initialize School Holiday Client
        
        Args:
            json_file_path: Path to the school holidays JSON file
        """
        # Ensure path is relative to web app root
        if not os.path.isabs(json_file_path):
            web_app_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.json_file_path = os.path.join(web_app_root, json_file_path)
        else:
            self.json_file_path = json_file_path
        self.logger = get_logger()
        self.school_holidays_data = None
        
        # Load school holidays data
        self._load_school_holidays_data()
        
        self.logger.info(f"SchoolHolidayClient initialized - JSON file: {json_file_path}")
    
    def _load_school_holidays_data(self):
        """Load school holidays data from JSON file"""
        try:
            if not os.path.exists(self.json_file_path):
                self.logger.error(f"School holidays JSON file not found: {self.json_file_path}")
                self.school_holidays_data = {"year": None, "terms": []}
                return
            
            with open(self.json_file_path, 'r') as file:
                self.school_holidays_data = json.load(file)
            
            self.logger.info(f"Loaded school holidays data for year {self.school_holidays_data.get('year', 'Unknown')}")
            self.logger.info(f"Found {len(self.school_holidays_data.get('terms', []))} terms")
            
        except Exception as e:
            self.logger.error(f"Error loading school holidays data: {e}")
            self.school_holidays_data = {"year": None, "terms": []}
    
    def get_school_holidays_for_state(self, state_code: str, year: int) -> List[Dict]:
        """
        Get school holidays for a specific state and year
        
        Args:
            state_code: Australian state code (VIC, NSW, QLD, etc.)
            year: Year to fetch holidays for
            
        Returns:
            List of school holiday dictionaries
        """
        if not self.school_holidays_data or not self.school_holidays_data.get('terms'):
            self.logger.warning("No school holidays data available")
            return []
        
        school_holidays = []
        
        for term in self.school_holidays_data.get('terms', []):
            term_name = term.get('term', 'Unknown Term')
            
            for range_data in term.get('ranges', []):
                if range_data.get('state', '').upper() == state_code.upper():
                    try:
                        # Parse dates
                        start_date = datetime.strptime(range_data['start'], '%Y-%m-%d').date()
                        end_date = datetime.strptime(range_data['end'], '%Y-%m-%d').date()
                        
                        # Check if this is for the requested year
                        if start_date.year == year or end_date.year == year:
                            school_holiday = {
                                'name': f"{term_name} School Holidays",
                                'type': 'School Holiday',
                                'importance': 'High',  # School holidays are high importance for family travel
                                'start_date': start_date,
                                'end_date': end_date,
                                'state_code': state_code,
                                'term': term_name,
                                'is_school_holiday': True,
                                'source': 'school_holidays.json'
                            }
                            
                            school_holidays.append(school_holiday)
                            
                    except (ValueError, KeyError) as e:
                        self.logger.warning(f"Error parsing school holiday date for {term_name} {state_code}: {e}")
                        continue
        
        self.logger.info(f"Found {len(school_holidays)} school holiday periods for {state_code} in {year}")
        return school_holidays
    
    def get_school_holiday_periods(self, state_code: str, start_date: date, end_date: date) -> List[Dict]:
        """
        Get school holiday periods within a date range for a specific state
        
        Args:
            state_code: Australian state code (VIC, NSW, QLD, etc.)
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of school holiday period dictionaries with extended dates
        """
        try:
            # Get all school holidays for the year(s) in the date range
            years = set()
            current_date = start_date
            while current_date <= end_date:
                years.add(current_date.year)
                current_date += timedelta(days=365)
            
            all_school_holidays = []
            for year in years:
                holidays = self.get_school_holidays_for_state(state_code, year)
                all_school_holidays.extend(holidays)
            
            # Filter school holidays within the date range and create extended periods
            school_holiday_periods = []
            for holiday in all_school_holidays:
                holiday_start = holiday['start_date']
                holiday_end = holiday['end_date']
                
                # Check if school holiday overlaps with analysis period
                if (holiday_start <= end_date and holiday_end >= start_date):
                    # Create extended period (±7 days around school holiday)
                    extended_start, extended_end = self._get_school_holiday_extended_dates(
                        holiday_start, holiday_end, extension_days=7
                    )
                    
                    school_holiday_period = {
                        'name': holiday['name'],
                        'type': holiday['type'],
                        'importance': holiday['importance'],
                        'start_date': holiday_start,
                        'end_date': holiday_end,
                        'extended_start': extended_start,
                        'extended_end': extended_end,
                        'state_code': state_code,
                        'term': holiday['term'],
                        'is_school_holiday': True,
                        'source': 'school_holidays.json'
                    }
                    
                    school_holiday_periods.append(school_holiday_period)
            
            self.logger.info(f"Found {len(school_holiday_periods)} school holiday periods for {state_code} in date range {start_date} to {end_date}")
            return school_holiday_periods
            
        except Exception as e:
            self.logger.error(f"Error getting school holiday periods for {state_code}: {e}")
            return []
    
    def get_school_holiday_periods_2month_forward(self, state_code: str, base_date: date = None) -> List[Dict]:
        """
        Get school holiday periods for a 2-month forward-looking window from a base date
        
        Args:
            state_code: Australian state code (VIC, NSW, QLD, etc.)
            base_date: Base date to start from (defaults to today)
            
        Returns:
            List of school holiday period dictionaries with extended dates
        """
        if base_date is None:
            base_date = date.today()
        
        # Calculate 2-month forward window
        start_date = base_date
        end_date = base_date + timedelta(days=60)  # 2 months forward
        
        self.logger.info(f"Getting 2-month forward school holiday periods for {state_code}: {start_date} to {end_date}")
        
        return self.get_school_holiday_periods(state_code, start_date, end_date)
    
    def _get_school_holiday_extended_dates(self, holiday_start: date, holiday_end: date, 
                                         extension_days: int = 7) -> Tuple[date, date]:
        """
        Calculate extended date range around school holiday period
        
        Args:
            holiday_start: Start date of school holiday period
            holiday_end: End date of school holiday period
            extension_days: Number of days to extend before and after
            
        Returns:
            Tuple of (extended_start_date, extended_end_date)
        """
        extended_start = holiday_start - timedelta(days=extension_days)
        extended_end = holiday_end + timedelta(days=extension_days)
        
        self.logger.debug(f"School holiday period: {holiday_start} to {holiday_end}")
        self.logger.debug(f"Extended period: {extended_start} to {extended_end}")
        
        return extended_start, extended_end
    
    def get_all_school_holidays_for_state(self, state_code: str) -> List[Dict]:
        """
        Get all school holidays for a state (all years in the data)
        
        Args:
            state_code: Australian state code
            
        Returns:
            List of all school holiday dictionaries for the state
        """
        if not self.school_holidays_data or not self.school_holidays_data.get('terms'):
            return []
        
        all_holidays = []
        data_year = self.school_holidays_data.get('year')
        
        if data_year:
            all_holidays = self.get_school_holidays_for_state(state_code, data_year)
        
        return all_holidays
    
    def get_school_holiday_stats(self) -> Dict:
        """
        Get statistics about the loaded school holidays data
        
        Returns:
            Dictionary with statistics about the school holidays data
        """
        if not self.school_holidays_data:
            return {"error": "No data loaded"}
        
        stats = {
            "year": self.school_holidays_data.get('year'),
            "total_terms": len(self.school_holidays_data.get('terms', [])),
            "source": self.school_holidays_data.get('source'),
            "terms": []
        }
        
        for term in self.school_holidays_data.get('terms', []):
            term_stats = {
                "name": term.get('term'),
                "state_count": len(term.get('ranges', [])),
                "states": [r.get('state') for r in term.get('ranges', [])]
            }
            stats["terms"].append(term_stats)
        
        return stats
    
    def test_data_integrity(self) -> bool:
        """
        Test the integrity of the loaded school holidays data
        
        Returns:
            True if data is valid, False otherwise
        """
        try:
            if not self.school_holidays_data:
                self.logger.error("No school holidays data loaded")
                return False
            
            required_fields = ['year', 'terms']
            for field in required_fields:
                if field not in self.school_holidays_data:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            terms = self.school_holidays_data.get('terms', [])
            if not terms:
                self.logger.error("No terms found in school holidays data")
                return False
            
            for term in terms:
                if 'term' not in term or 'ranges' not in term:
                    self.logger.error(f"Invalid term structure: {term}")
                    return False
                
                for range_data in term.get('ranges', []):
                    required_range_fields = ['state', 'start', 'end']
                    for field in required_range_fields:
                        if field not in range_data:
                            self.logger.error(f"Missing required field in range: {field}")
                            return False
                    
                    # Validate date format
                    try:
                        datetime.strptime(range_data['start'], '%Y-%m-%d')
                        datetime.strptime(range_data['end'], '%Y-%m-%d')
                    except ValueError as e:
                        self.logger.error(f"Invalid date format in range: {e}")
                        return False
            
            self.logger.info("School holidays data integrity check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during data integrity check: {e}")
            return False


if __name__ == "__main__":
    # Test the school holiday client
    client = SchoolHolidayClient()
    
    print("🧪 Testing School Holiday Client")
    print("=" * 50)
    
    # Test data integrity
    if client.test_data_integrity():
        print("✅ Data integrity check passed")
        
        # Get stats
        stats = client.get_school_holiday_stats()
        print(f"📊 Stats: {stats}")
        
        # Test for different states
        test_states = ['TAS', 'QLD', 'NSW', 'VIC']
        year = 2025
        
        for state in test_states:
            print(f"\n🏛️  Testing {state}:")
            holidays = client.get_school_holidays_for_state(state, year)
            print(f"   📅 Found {len(holidays)} school holiday periods")
            
            for holiday in holidays:
                print(f"   ✅ {holiday['name']} ({holiday['start_date']} to {holiday['end_date']})")
        
        # Test 2-month forward periods
        print(f"\n🔮 Testing 2-month forward periods:")
        for state in test_states:
            periods = client.get_school_holiday_periods_2month_forward(state)
            print(f"   {state}: {len(periods)} periods in next 2 months")
            
    else:
        print("❌ Data integrity check failed")
