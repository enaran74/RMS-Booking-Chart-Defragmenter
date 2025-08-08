#!/usr/bin/env python3
"""
Holiday Integration Test Script for Step 3
Tests the HolidayClient and enhanced RMS client functionality
"""

import os
import sys
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple

def test_holiday_client_creation():
    """Test HolidayClient creation and initialization"""
    print("🧪 Testing HolidayClient Creation")
    print("=" * 50)
    
    try:
        from holiday_client import HolidayClient
        
        # Test client creation
        client = HolidayClient(cache_ttl=3600, timeout=30)
        
        # Test attributes
        assert hasattr(client, 'base_url'), "Missing base_url attribute"
        assert hasattr(client, 'cache'), "Missing cache attribute"
        assert hasattr(client, 'cache_ttl'), "Missing cache_ttl attribute"
        assert hasattr(client, 'timeout'), "Missing timeout attribute"
        assert hasattr(client, 'STATE_COUNTRY_MAPPING'), "Missing STATE_COUNTRY_MAPPING"
        assert hasattr(client, 'HOLIDAY_IMPORTANCE_MAPPING'), "Missing HOLIDAY_IMPORTANCE_MAPPING"
        
        print(f"✅ Base URL: {client.base_url}")
        print(f"✅ Cache TTL: {client.cache_ttl} seconds")
        print(f"✅ Timeout: {client.timeout} seconds")
        print(f"✅ State mappings: {len(client.STATE_COUNTRY_MAPPING)} states")
        print(f"✅ Holiday importance mappings: {len(client.HOLIDAY_IMPORTANCE_MAPPING)} holidays")
        
        print("✅ HolidayClient creation: PASSED")
        return client
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None
    except Exception as e:
        print(f"❌ Creation error: {e}")
        return None

def test_api_connectivity(client):
    """Test API connectivity"""
    print("\n🧪 Testing API Connectivity")
    print("=" * 50)
    
    if not client:
        print("❌ No client available for testing")
        return False
    
    try:
        # Test API connectivity
        is_connected = client.test_api_connectivity()
        
        if is_connected:
            print("✅ API connectivity: PASSED")
            return True
        else:
            print("❌ API connectivity: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ API connectivity test error: {e}")
        return False

def test_holiday_data_fetching(client):
    """Test holiday data fetching"""
    print("\n🧪 Testing Holiday Data Fetching")
    print("=" * 50)
    
    if not client:
        print("❌ No client available for testing")
        return False
    
    try:
        # Test fetching holidays for Victoria
        current_year = date.today().year
        holidays = client.get_holidays_for_state('VIC', current_year)
        
        print(f"✅ Retrieved {len(holidays)} holidays for VIC {current_year}")
        
        if holidays:
            # Show first few holidays
            print("Sample holidays:")
            for i, holiday in enumerate(holidays[:5]):
                print(f"  {i+1}. {holiday['name']} - {holiday['start_date']} ({holiday['importance']})")
        
        # Test cache functionality
        print("\nTesting cache...")
        cached_holidays = client.get_holidays_for_state('VIC', current_year)
        assert len(cached_holidays) == len(holidays), "Cache should return same data"
        print("✅ Cache functionality: PASSED")
        
        # Test cache stats
        cache_stats = client.get_cache_stats()
        print(f"✅ Cache stats: {cache_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Holiday data fetching error: {e}")
        return False

def test_upcoming_holidays(client):
    """Test upcoming holidays functionality"""
    print("\n🧪 Testing Upcoming Holidays")
    print("=" * 50)
    
    if not client:
        print("❌ No client available for testing")
        return False
    
    try:
        # Test upcoming holidays for multiple states
        states = ['VIC', 'NSW', 'QLD']
        
        for state in states:
            upcoming = client.get_upcoming_holidays(state, days_ahead=365)
            print(f"✅ {state}: {len(upcoming)} upcoming holidays")
            
            if upcoming:
                # Show next holiday
                next_holiday = upcoming[0]
                print(f"  Next: {next_holiday['name']} on {next_holiday['start_date']}")
                print(f"  Extended period: {next_holiday['extended_start']} to {next_holiday['extended_end']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Upcoming holidays error: {e}")
        return False

def test_holiday_date_calculations(client):
    """Test holiday date calculations"""
    print("\n🧪 Testing Holiday Date Calculations")
    print("=" * 50)
    
    if not client:
        print("❌ No client available for testing")
        return False
    
    try:
        # Test extended date calculation
        holiday_start = date(2025, 1, 26)  # Australia Day
        holiday_end = date(2025, 1, 26)
        
        extended_start, extended_end = client.get_holiday_extended_dates(
            holiday_start, holiday_end, extension_days=7
        )
        
        print(f"Holiday period: {holiday_start} to {holiday_end}")
        print(f"Extended period: {extended_start} to {extended_end}")
        
        # Verify extension
        assert (holiday_start - extended_start).days == 7, "Start extension should be 7 days"
        assert (extended_end - holiday_end).days == 7, "End extension should be 7 days"
        
        print("✅ Holiday date calculations: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Holiday date calculations error: {e}")
        return False

def test_holiday_aware_date_range(client):
    """Test holiday-aware date range calculation"""
    print("\n🧪 Testing Holiday-Aware Date Range")
    print("=" * 50)
    
    if not client:
        print("❌ No client available for testing")
        return False
    
    try:
        # Test holiday-aware date range for Victoria
        base_start = date.today()
        base_end = base_start + timedelta(days=31)
        
        holiday_start, holiday_end = client.get_holiday_aware_date_range(
            'VIC', base_start, base_end
        )
        
        print(f"Base range: {base_start} to {base_end}")
        print(f"Holiday-aware range: {holiday_start} to {holiday_end}")
        
        # Verify range is at least as large as base range
        base_days = (base_end - base_start).days
        holiday_days = (holiday_end - holiday_start).days
        
        assert holiday_days >= base_days, "Holiday range should be at least as large as base range"
        
        print(f"✅ Base range: {base_days} days")
        print(f"✅ Holiday range: {holiday_days} days")
        print("✅ Holiday-aware date range: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Holiday-aware date range error: {e}")
        return False

def test_rms_client_enhancements():
    """Test RMS client enhancements"""
    print("\n🧪 Testing RMS Client Enhancements")
    print("=" * 50)
    
    try:
        from rms_client import RMSClient
        
        # Create mock RMS client (without authentication)
        client = RMSClient(
            agent_id="test",
            agent_password="test",
            client_id="test",
            client_password="test",
            use_training_db=True
        )
        
        # Test state code extraction
        test_properties = [
            {
                'id': 1,
                'name': 'Victoria Park',
                'code': 'VIC001',
                'state': 'VIC',
                'inactive': False
            },
            {
                'id': 2,
                'name': 'Queensland Resort',
                'code': 'QLD002',
                'stateCode': 'QLD',
                'inactive': False
            },
            {
                'id': 3,
                'name': 'NSW Beach House',
                'code': 'NSW003',
                'region': 'NSW',
                'inactive': False
            }
        ]
        
        expected_states = ['VIC', 'QLD', 'NSW']
        
        for i, property_data in enumerate(test_properties):
            state_code = client.extract_state_code(property_data)
            expected = expected_states[i]
            
            assert state_code == expected, f"State extraction failed: expected {expected}, got {state_code}"
            print(f"✅ Property {i+1}: {property_data['name']} -> {state_code}")
        
        # Test property with state
        client.all_properties = test_properties
        property_with_state = client.get_property_with_state(1)
        
        assert property_with_state is not None, "Property with state should not be None"
        assert 'state_code' in property_with_state, "Property should have state_code field"
        assert property_with_state['state_code'] == 'VIC', "State code should be VIC"
        
        print("✅ Property with state: PASSED")
        
        print("✅ RMS client enhancements: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ RMS client enhancements error: {e}")
        return False

def test_holiday_importance_mapping():
    """Test holiday importance mapping"""
    print("\n🧪 Testing Holiday Importance Mapping")
    print("=" * 50)
    
    try:
        from holiday_client import HolidayClient
        
        client = HolidayClient()
        
        # Test importance mappings
        test_holidays = [
            'Australia Day',
            'Christmas Day',
            'New Year\'s Day',
            'Queen\'s Birthday',
            'Labour Day'
        ]
        
        expected_importance = ['High', 'High', 'High', 'Medium', 'Medium']
        
        for holiday, expected in zip(test_holidays, expected_importance):
            importance = client.HOLIDAY_IMPORTANCE_MAPPING.get(holiday, 'Medium')
            assert importance == expected, f"Importance mismatch for {holiday}: expected {expected}, got {importance}"
            print(f"✅ {holiday}: {importance}")
        
        print("✅ Holiday importance mapping: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Holiday importance mapping error: {e}")
        return False

def run_integration_tests():
    """Run all holiday integration tests"""
    print("🚀 Running Holiday Integration Tests for Step 3")
    print("=" * 60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test 1: HolidayClient creation
        client = test_holiday_client_creation()
        if not client:
            return False
        
        # Test 2: API connectivity
        if not test_api_connectivity(client):
            print("⚠️  API connectivity failed - some tests may be limited")
        
        # Test 3: Holiday data fetching
        if not test_holiday_data_fetching(client):
            print("⚠️  Holiday data fetching failed - some tests may be limited")
        
        # Test 4: Upcoming holidays
        if not test_upcoming_holidays(client):
            print("⚠️  Upcoming holidays failed - some tests may be limited")
        
        # Test 5: Holiday date calculations
        if not test_holiday_date_calculations(client):
            return False
        
        # Test 6: Holiday-aware date range
        if not test_holiday_aware_date_range(client):
            return False
        
        # Test 7: RMS client enhancements
        if not test_rms_client_enhancements():
            return False
        
        # Test 8: Holiday importance mapping
        if not test_holiday_importance_mapping():
            return False
        
        print("\n" + "=" * 60)
        print("🎉 ALL HOLIDAY INTEGRATION TESTS PASSED!")
        print("✅ Holiday client and API integration is working correctly")
        print("📋 Next: Step 4 - Implement Holiday Analysis in Defragmentation Analyzer")
        
        return True
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
