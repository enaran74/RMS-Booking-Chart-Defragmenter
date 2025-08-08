#!/usr/bin/env python3
"""
Holiday Client for Nager.Date API Integration
Fetches holiday data and provides holiday-aware date range calculations
"""

import requests
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from utils import get_logger

class HolidayClient:
    """Client for fetching and managing holiday data from Nager.Date API"""
    
    def __init__(self, cache_ttl: int = 86400, timeout: int = 30):
        """
        Initialize Holiday Client
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 24 hours)
            timeout: API request timeout in seconds (default: 30)
        """
        self.base_url = "https://date.nager.at/api/v3"
        self.cache = {}
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self.logger = get_logger()
        
        # Australian state to country mapping
        self.STATE_COUNTRY_MAPPING = {
            'VIC': 'AU', 'TAS': 'AU', 'ACT': 'AU', 'NSW': 'AU',
            'QLD': 'AU', 'NT': 'AU', 'SA': 'AU', 'WA': 'AU'
        }
        
        # Holiday importance mapping
        self.HOLIDAY_IMPORTANCE_MAPPING = {
            'Australia Day': 'High',
            'New Year\'s Day': 'High',
            'Christmas Day': 'High',
            'Boxing Day': 'High',
            'Good Friday': 'High',
            'Easter Monday': 'High',
            'ANZAC Day': 'High',
            'Queen\'s Birthday': 'Medium',
            'Labour Day': 'Medium',
            'Easter Sunday': 'Medium',
            'Easter Saturday': 'Medium'
        }
        
        self.logger.info(f"HolidayClient initialized - Cache TTL: {cache_ttl}s, Timeout: {timeout}s")
    
    def get_holidays_for_state(self, state_code: str, year: int) -> List[Dict]:
        """
        Fetch holidays for a specific state and year
        
        Args:
            state_code: Australian state code (VIC, NSW, QLD, etc.)
            year: Year to fetch holidays for
            
        Returns:
            List of holiday dictionaries
        """
        cache_key = f"{state_code}_{year}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            self.logger.debug(f"Returning cached holidays for {state_code} {year}")
            return self.cache[cache_key]['data']
        
        # Get country code for state
        country_code = self.STATE_COUNTRY_MAPPING.get(state_code.upper())
        if not country_code:
            self.logger.warning(f"Unknown state code: {state_code}")
            return []
        
        try:
            self.logger.info(f"Fetching holidays for {state_code} ({country_code}) in {year}")
            
            # Fetch holidays from API
            url = f"{self.base_url}/PublicHolidays/{year}/{country_code}"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                holidays = response.json()
                self.logger.info(f"Retrieved {len(holidays)} holidays for {state_code} {year}")
                
                # Process and cache holidays
                processed_holidays = self._process_holidays(holidays, state_code)
                self._cache_data(cache_key, processed_holidays)
                
                return processed_holidays
            else:
                self.logger.error(f"API request failed: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.Timeout:
            self.logger.error(f"API request timeout for {state_code} {year}")
            return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request error for {state_code} {year}: {e}")
            return []
    
    def get_holiday_periods(self, start_date: date, end_date: date, state_code: str) -> List[Dict]:
        """
        Get holiday periods within a date range for a specific state
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            state_code: Australian state code (VIC, NSW, QLD, etc.)
            
        Returns:
            List of holiday period dictionaries with extended dates
        """
        try:
            # Get all holidays for the year(s) in the date range
            years = set()
            current_date = start_date
            while current_date <= end_date:
                years.add(current_date.year)
                current_date += timedelta(days=365)
            
            all_holidays = []
            for year in years:
                holidays = self.get_holidays_for_state(state_code, year)
                all_holidays.extend(holidays)
            
            # Filter holidays within the date range and create extended periods
            holiday_periods = []
            for holiday in all_holidays:
                holiday_start = holiday['start_date']
                holiday_end = holiday['end_date']
                
                # Check if holiday overlaps with analysis period
                if (holiday_start <= end_date and holiday_end >= start_date):
                    # Create extended period (±7 days around holiday)
                    extended_start, extended_end = self.get_holiday_extended_dates(
                        holiday_start, holiday_end, extension_days=7
                    )
                    
                    holiday_period = {
                        'name': holiday['name'],
                        'type': holiday['type'],
                        'importance': holiday['importance'],
                        'start_date': holiday_start,
                        'end_date': holiday_end,
                        'extended_start': extended_start,
                        'extended_end': extended_end,
                        'state_code': state_code
                    }
                    
                    holiday_periods.append(holiday_period)
            
            self.logger.info(f"Found {len(holiday_periods)} holiday periods for {state_code} in date range {start_date} to {end_date}")
            return holiday_periods
            
        except Exception as e:
            self.logger.error(f"Error getting holiday periods for {state_code}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching holidays for {state_code} {year}: {e}")
            return []
    
    def get_holiday_extended_dates(self, holiday_start: date, holiday_end: date, 
                                 extension_days: int = 7) -> Tuple[date, date]:
        """
        Calculate extended date range around holiday period
        
        Args:
            holiday_start: Start date of holiday period
            holiday_end: End date of holiday period
            extension_days: Number of days to extend before and after
            
        Returns:
            Tuple of (extended_start_date, extended_end_date)
        """
        extended_start = holiday_start - timedelta(days=extension_days)
        extended_end = holiday_end + timedelta(days=extension_days)
        
        self.logger.debug(f"Holiday period: {holiday_start} to {holiday_end}")
        self.logger.debug(f"Extended period: {extended_start} to {extended_end}")
        
        return extended_start, extended_end
    
    def is_holiday_period(self, check_date: date, state_code: str) -> Optional[Dict]:
        """
        Check if a date falls within a holiday period
        
        Args:
            check_date: Date to check
            state_code: Australian state code
            
        Returns:
            Holiday data if date is a holiday, None otherwise
        """
        year = check_date.year
        
        # Get holidays for the year
        holidays = self.get_holidays_for_state(state_code, year)
        
        # Check if date matches any holiday
        for holiday in holidays:
            holiday_date = holiday['start_date']
            if check_date == holiday_date:
                return holiday
        
        return None
    
    def get_upcoming_holidays(self, state_code: str, days_ahead: int = 365) -> List[Dict]:
        """
        Get upcoming holidays within specified days
        
        Args:
            state_code: Australian state code
            days_ahead: Number of days ahead to look for holidays
            
        Returns:
            List of upcoming holiday periods
        """
        today = date.today()
        end_date = today + timedelta(days=days_ahead)
        
        upcoming_holidays = []
        
        # Get holidays for current and next year
        current_year = today.year
        next_year = current_year + 1
        
        for year in [current_year, next_year]:
            holidays = self.get_holidays_for_state(state_code, year)
            
            for holiday in holidays:
                holiday_date = holiday['start_date']
                
                # Check if holiday is within the specified range
                if today <= holiday_date <= end_date:
                    # Calculate extended period
                    extended_start, extended_end = self.get_holiday_extended_dates(
                        holiday_date, holiday_date
                    )
                    
                    # Add extended period to holiday data
                    holiday['extended_start'] = extended_start
                    holiday['extended_end'] = extended_end
                    holiday['state_code'] = state_code
                    holiday['country_code'] = self.STATE_COUNTRY_MAPPING.get(state_code.upper(), 'AU')
                    
                    upcoming_holidays.append(holiday)
        
        # Sort by date
        upcoming_holidays.sort(key=lambda x: x['start_date'])
        
        self.logger.info(f"Found {len(upcoming_holidays)} upcoming holidays for {state_code}")
        return upcoming_holidays
    
    def get_holiday_aware_date_range(self, state_code: str, base_start_date: date = None, 
                                   base_end_date: date = None) -> Tuple[date, date]:
        """
        Calculate holiday-aware date range for a property
        
        Args:
            state_code: Australian state code
            base_start_date: Base start date (default: today)
            base_end_date: Base end date (default: today + 31 days)
            
        Returns:
            Tuple of (holiday_aware_start_date, holiday_aware_end_date)
        """
        if base_start_date is None:
            base_start_date = date.today()
        if base_end_date is None:
            base_end_date = base_start_date + timedelta(days=31)
        
        # Get upcoming holidays
        upcoming_holidays = self.get_upcoming_holidays(state_code, days_ahead=365)
        
        # Find holidays that overlap with or are near the base date range
        relevant_holidays = []
        for holiday in upcoming_holidays:
            extended_start = holiday['extended_start']
            extended_end = holiday['extended_end']
            
            # Check if holiday period overlaps with or is near base range
            if (extended_start <= base_end_date and extended_end >= base_start_date):
                relevant_holidays.append(holiday)
        
        if not relevant_holidays:
            self.logger.debug(f"No relevant holidays found for {state_code}, using base range")
            return base_start_date, base_end_date
        
        # Calculate extended range to include all relevant holidays
        min_start = min(holiday['extended_start'] for holiday in relevant_holidays)
        max_end = max(holiday['extended_end'] for holiday in relevant_holidays)
        
        # Ensure we don't go too far back in time
        final_start = max(min_start, base_start_date - timedelta(days=7))
        final_end = max_end
        
        self.logger.info(f"Holiday-aware date range for {state_code}: {final_start} to {final_end}")
        self.logger.info(f"Relevant holidays: {[h['name'] for h in relevant_holidays]}")
        
        return final_start, final_end
    
    def _process_holidays(self, holidays: List[Dict], state_code: str) -> List[Dict]:
        """
        Process raw holiday data from API
        
        Args:
            holidays: Raw holiday data from API
            state_code: Australian state code
            
        Returns:
            Processed holiday data
        """
        processed_holidays = []
        
        for holiday in holidays:
            # Parse date
            try:
                holiday_date = datetime.strptime(holiday['date'], '%Y-%m-%d').date()
            except ValueError:
                self.logger.warning(f"Invalid date format: {holiday['date']}")
                continue
            
            # Determine importance
            importance = self.HOLIDAY_IMPORTANCE_MAPPING.get(holiday['name'], 'Medium')
            
            # Create processed holiday data
            processed_holiday = {
                'name': holiday['name'],
                'type': 'Public Holiday',
                'importance': importance,
                'start_date': holiday_date,
                'end_date': holiday_date,
                'state_code': state_code,
                'country_code': self.STATE_COUNTRY_MAPPING.get(state_code.upper(), 'AU'),
                'api_data': holiday  # Keep original API data for reference
            }
            
            processed_holidays.append(processed_holiday)
        
        return processed_holidays
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key]['timestamp']
        current_time = time.time()
        
        return (current_time - cache_time) < self.cache_ttl
    
    def _cache_data(self, cache_key: str, data: List[Dict]):
        """Cache data with timestamp"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        self.logger.debug(f"Cached data for key: {cache_key}")
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        self.logger.info("Holiday cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'cache_ttl': self.cache_ttl,
            'cached_keys': list(self.cache.keys())
        }
    
    def test_api_connectivity(self) -> bool:
        """
        Test API connectivity
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Test with a simple endpoint
            url = f"{self.base_url}/AvailableCountries"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                self.logger.info("API connectivity test: PASSED")
                return True
            else:
                self.logger.error(f"API connectivity test failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"API connectivity test failed: {e}")
            return False
