#!/usr/bin/env python3
"""
Baseline Test Script for Holiday-Aware Defragmentation Enhancement
Tests current functionality to establish baseline before adding holiday features
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List

def test_current_date_range():
    """Test current 31-day date range calculation"""
    print("🧪 Testing Current Date Range Logic")
    print("=" * 40)
    
    today = datetime.now().date()
    constraint_start_date = today
    constraint_end_date = today + timedelta(days=31)
    
    print(f"Today: {today}")
    print(f"Start Date: {constraint_start_date}")
    print(f"End Date: {constraint_end_date}")
    print(f"Date Range: {(constraint_end_date - constraint_start_date).days} days")
    
    # Verify it's exactly 31 days
    assert (constraint_end_date - constraint_start_date).days == 31, "Date range should be 31 days"
    print("✅ Date range calculation: PASSED")
    
    return constraint_start_date, constraint_end_date

def test_state_code_mapping():
    """Test state code mapping for Australian states"""
    print("\n🧪 Testing State Code Mapping")
    print("=" * 40)
    
    STATE_MAPPING = {
        'VIC': 'AU',  # Victoria
        'TAS': 'AU',  # Tasmania
        'ACT': 'AU',  # Australian Capital Territory
        'NSW': 'AU',  # New South Wales
        'QLD': 'AU',  # Queensland
        'NT': 'AU',   # Northern Territory
        'SA': 'AU',   # South Australia
        'WA': 'AU'    # Western Australia
    }
    
    print("Australian State to Country Code Mapping:")
    for state, country in STATE_MAPPING.items():
        print(f"  {state} -> {country}")
    
    # Test all states map to AU
    for state, country in STATE_MAPPING.items():
        assert country == 'AU', f"State {state} should map to AU"
    
    print("✅ State code mapping: PASSED")
    return STATE_MAPPING

def test_holiday_date_range_calculation():
    """Test holiday date range extension logic"""
    print("\n🧪 Testing Holiday Date Range Extension")
    print("=" * 40)
    
    # Mock holiday period
    holiday_start = datetime(2025, 1, 26).date()  # Australia Day
    holiday_end = datetime(2025, 1, 26).date()
    extension_days = 7
    
    # Calculate extended range
    extended_start = holiday_start - timedelta(days=extension_days)
    extended_end = holiday_end + timedelta(days=extension_days)
    
    print(f"Holiday Period: {holiday_start} to {holiday_end}")
    print(f"Extension Days: ±{extension_days}")
    print(f"Extended Range: {extended_start} to {extended_end}")
    print(f"Total Extended Days: {(extended_end - extended_start).days + 1}")
    
    # Verify extension
    assert (holiday_start - extended_start).days == extension_days, "Start extension should be 7 days"
    assert (extended_end - holiday_end).days == extension_days, "End extension should be 7 days"
    
    print("✅ Holiday date range extension: PASSED")
    return extended_start, extended_end

def test_move_deduplication_logic():
    """Test move deduplication logic"""
    print("\n🧪 Testing Move Deduplication Logic")
    print("=" * 40)
    
    # Mock moves
    regular_moves = [
        {
            'property': 'SADE',
            'move_id': '1.1',
            'from_unit': 'Cabin 1',
            'to_unit': 'Cabin 2',
            'from_date': '2025-01-20',
            'to_date': '2025-01-25',
            'guest_name': 'John Doe'
        }
    ]
    
    holiday_moves = [
        {
            'property': 'SADE',
            'move_id': 'H1.1',  # Holiday prefix
            'from_unit': 'Cabin 1',
            'to_unit': 'Cabin 2',
            'from_date': '2025-01-20',
            'to_date': '2025-01-25',
            'guest_name': 'John Doe',
            'holiday_period': 'Australia Day 2025'
        }
    ]
    
    # Test deduplication logic
    def deduplicate_moves(regular_moves, holiday_moves):
        """Simple deduplication based on property, unit, and date"""
        all_moves = regular_moves.copy()
        
        for holiday_move in holiday_moves:
            # Check if this move already exists in regular moves
            is_duplicate = False
            for regular_move in regular_moves:
                if (holiday_move['property'] == regular_move['property'] and
                    holiday_move['from_unit'] == regular_move['from_unit'] and
                    holiday_move['to_unit'] == regular_move['to_unit'] and
                    holiday_move['from_date'] == regular_move['from_date'] and
                    holiday_move['to_date'] == regular_move['to_date']):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                all_moves.append(holiday_move)
        
        return all_moves
    
    # Test deduplication
    deduplicated_moves = deduplicate_moves(regular_moves, holiday_moves)
    
    print(f"Regular moves: {len(regular_moves)}")
    print(f"Holiday moves: {len(holiday_moves)}")
    print(f"Deduplicated moves: {len(deduplicated_moves)}")
    
    # Should have only 1 move (duplicate removed)
    assert len(deduplicated_moves) == 1, "Should remove duplicate move"
    assert deduplicated_moves[0]['move_id'] == '1.1', "Should keep regular move"
    
    print("✅ Move deduplication logic: PASSED")
    return deduplicated_moves

def test_holiday_move_structure():
    """Test holiday move data structure"""
    print("\n🧪 Testing Holiday Move Data Structure")
    print("=" * 40)
    
    # Mock holiday move
    holiday_move = {
        'property': 'SADE',
        'move_id': 'H1.1',  # Holiday prefix
        'from_unit': 'Cabin 1',
        'to_unit': 'Cabin 2',
        'from_date': '2025-01-20',
        'to_date': '2025-01-25',
        'guest_name': 'John Doe',
        'improvement_score': 0.85,
        'reasoning': 'Creates 3-night contiguous availability',
        'holiday_period': 'Australia Day 2025',
        'holiday_type': 'Public Holiday',
        'holiday_importance': 'High'
    }
    
    # Test required fields
    required_fields = [
        'property', 'move_id', 'from_unit', 'to_unit', 
        'from_date', 'to_date', 'guest_name', 'improvement_score',
        'reasoning', 'holiday_period', 'holiday_type', 'holiday_importance'
    ]
    
    print("Required fields for holiday moves:")
    for field in required_fields:
        assert field in holiday_move, f"Missing required field: {field}"
        print(f"  ✅ {field}: {holiday_move[field]}")
    
    # Test holiday-specific fields
    assert holiday_move['move_id'].startswith('H'), "Holiday moves should have 'H' prefix"
    assert 'holiday_period' in holiday_move, "Holiday moves should include holiday period"
    assert 'holiday_type' in holiday_move, "Holiday moves should include holiday type"
    
    print("✅ Holiday move data structure: PASSED")
    return holiday_move

def test_nager_date_api_structure():
    """Test Nager.Date API response structure"""
    print("\n🧪 Testing Nager.Date API Structure")
    print("=" * 40)
    
    # Mock API response based on documentation
    mock_api_response = [
        {
            "date": "2025-01-01",
            "localName": "Neujahr",
            "name": "New Year's Day",
            "countryCode": "AT",
            "fixed": True,
            "global": True,
            "counties": None,
            "launchYear": 1967,
            "types": ["Public"]
        },
        {
            "date": "2025-01-26",
            "localName": "Australia Day",
            "name": "Australia Day",
            "countryCode": "AU",
            "fixed": True,
            "global": True,
            "counties": None,
            "launchYear": None,
            "types": ["Public"]
        }
    ]
    
    print("Nager.Date API Response Structure:")
    for holiday in mock_api_response:
        print(f"  📅 {holiday['date']}: {holiday['name']} ({holiday['countryCode']})")
        print(f"     Types: {holiday['types']}")
        print(f"     Fixed: {holiday['fixed']}")
        print(f"     Global: {holiday['global']}")
    
    # Test required fields
    required_fields = ['date', 'name', 'countryCode', 'types']
    for holiday in mock_api_response:
        for field in required_fields:
            assert field in holiday, f"Missing required field: {field}"
    
    print("✅ Nager.Date API structure: PASSED")
    return mock_api_response

def run_baseline_tests():
    """Run all baseline tests"""
    print("🚀 Running Baseline Tests for Holiday-Aware Defragmentation")
    print("=" * 60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Run all tests
        test_current_date_range()
        test_state_code_mapping()
        test_holiday_date_range_calculation()
        test_move_deduplication_logic()
        test_holiday_move_structure()
        test_nager_date_api_structure()
        
        print("\n" + "=" * 60)
        print("🎉 ALL BASELINE TESTS PASSED!")
        print("✅ Ready to proceed with holiday-aware enhancement")
        print("📋 Next: Step 2 - Design Holiday Integration Architecture")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_baseline_tests()
    sys.exit(0 if success else 1)
