#!/usr/bin/env python3
"""
Architecture Validation Test Script for Step 2
Tests the holiday integration architecture design before implementation
"""

import os
import sys
import time
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple

def test_holiday_client_interface():
    """Test HolidayClient interface design"""
    print("🧪 Testing HolidayClient Interface Design")
    print("=" * 50)
    
    # Mock HolidayClient interface
    class MockHolidayClient:
        def __init__(self):
            self.base_url = "https://date.nager.at/api/v3"
            self.cache = {}
            self.cache_ttl = 86400  # 24 hours
        
        def get_holidays_for_state(self, state_code: str, year: int) -> List[Dict]:
            """Fetch holidays for a specific state and year"""
            return []
        
        def get_holiday_extended_dates(self, holiday_start: date, holiday_end: date, 
                                     extension_days: int = 7) -> Tuple[date, date]:
            """Calculate extended date range around holiday period"""
            extended_start = holiday_start - timedelta(days=extension_days)
            extended_end = holiday_end + timedelta(days=extension_days)
            return extended_start, extended_end
        
        def is_holiday_period(self, check_date: date, state_code: str) -> Optional[Dict]:
            """Check if a date falls within a holiday period"""
            return None
        
        def get_upcoming_holidays(self, state_code: str, days_ahead: int = 365) -> List[Dict]:
            """Get upcoming holidays within specified days"""
            return []
    
    # Test interface
    client = MockHolidayClient()
    
    # Test method signatures
    assert hasattr(client, 'get_holidays_for_state'), "Missing get_holidays_for_state method"
    assert hasattr(client, 'get_holiday_extended_dates'), "Missing get_holiday_extended_dates method"
    assert hasattr(client, 'is_holiday_period'), "Missing is_holiday_period method"
    assert hasattr(client, 'get_upcoming_holidays'), "Missing get_upcoming_holidays method"
    
    # Test extended date calculation
    holiday_start = date(2025, 1, 26)
    holiday_end = date(2025, 1, 26)
    extended_start, extended_end = client.get_holiday_extended_dates(holiday_start, holiday_end, 7)
    
    assert extended_start == date(2025, 1, 19), "Extended start date calculation failed"
    assert extended_end == date(2025, 2, 2), "Extended end date calculation failed"
    
    print("✅ HolidayClient interface: PASSED")
    return client

def test_state_code_extraction_strategy():
    """Test state code extraction strategy"""
    print("\n🧪 Testing State Code Extraction Strategy")
    print("=" * 50)
    
    # Mock property data with different state field scenarios
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
        },
        {
            'id': 4,
            'name': 'SA Desert Lodge',
            'code': 'SA004',
            'location': 'SA',
            'inactive': False
        },
        {
            'id': 5,
            'name': 'WA Coastal Resort',
            'code': 'WA005',
            'address': 'WA',
            'inactive': False
        },
        {
            'id': 6,
            'name': 'TAS Mountain Lodge',
            'code': 'TAS006',
            'inactive': False
        }
    ]
    
    # State code extraction function
    def extract_state_code(property_data: Dict) -> Optional[str]:
        """Extract state code from property data"""
        STATE_COUNTRY_MAPPING = {
            'VIC': 'AU', 'TAS': 'AU', 'ACT': 'AU', 'NSW': 'AU',
            'QLD': 'AU', 'NT': 'AU', 'SA': 'AU', 'WA': 'AU'
        }
        
        # Try multiple possible field names
        state_fields = ['state', 'stateCode', 'region', 'location', 'address']
        
        for field in state_fields:
            if field in property_data and property_data[field]:
                state_code = str(property_data[field]).upper()
                if state_code in STATE_COUNTRY_MAPPING:
                    return state_code
        
        # Fallback: extract from property name or code
        property_name = property_data.get('name', '').upper()
        property_code = property_data.get('code', '').upper()
        
        # Look for state abbreviations in name/code
        for state_code in STATE_COUNTRY_MAPPING.keys():
            if state_code in property_name or state_code in property_code:
                return state_code
        
        return None
    
    # Test extraction
    expected_states = ['VIC', 'QLD', 'NSW', 'SA', 'WA', 'TAS']
    extracted_states = []
    
    for i, property_data in enumerate(test_properties):
        state_code = extract_state_code(property_data)
        extracted_states.append(state_code)
        print(f"Property {i+1}: {property_data['name']} -> {state_code}")
    
    # Verify all states were extracted
    for expected, extracted in zip(expected_states, extracted_states):
        assert extracted == expected, f"State extraction failed: expected {expected}, got {extracted}"
    
    print("✅ State code extraction strategy: PASSED")
    return extracted_states

def test_holiday_data_structures():
    """Test holiday data structures"""
    print("\n🧪 Testing Holiday Data Structures")
    print("=" * 50)
    
    # Test holiday period structure
    holiday_period = {
        'name': 'Australia Day 2025',
        'type': 'Public Holiday',
        'importance': 'High',
        'start_date': date(2025, 1, 26),
        'end_date': date(2025, 1, 26),
        'extended_start': date(2025, 1, 19),
        'extended_end': date(2025, 2, 2),
        'state_code': 'VIC',
        'country_code': 'AU'
    }
    
    # Test required fields
    required_fields = [
        'name', 'type', 'importance', 'start_date', 'end_date',
        'extended_start', 'extended_end', 'state_code', 'country_code'
    ]
    
    for field in required_fields:
        assert field in holiday_period, f"Missing required field: {field}"
        print(f"  ✅ {field}: {holiday_period[field]}")
    
    # Test date logic
    assert holiday_period['extended_start'] < holiday_period['start_date'], "Extended start should be before holiday start"
    assert holiday_period['extended_end'] > holiday_period['end_date'], "Extended end should be after holiday end"
    
    # Test enhanced move structure
    enhanced_move = {
        # Regular move fields
        'property': 'SADE',
        'move_id': 'H1.1',  # Holiday prefix
        'from_unit': 'Cabin 1',
        'to_unit': 'Cabin 2',
        'from_date': '2025-01-20',
        'to_date': '2025-01-25',
        'guest_name': 'John Doe',
        'improvement_score': 0.85,
        'reasoning': 'Creates 3-night contiguous availability',
        
        # Holiday-specific fields
        'holiday_period': 'Australia Day 2025',
        'holiday_type': 'Public Holiday',
        'holiday_importance': 'High',
        'is_holiday_move': True
    }
    
    # Test move structure
    move_required_fields = [
        'property', 'move_id', 'from_unit', 'to_unit', 'from_date', 'to_date',
        'guest_name', 'improvement_score', 'reasoning', 'holiday_period',
        'holiday_type', 'holiday_importance', 'is_holiday_move'
    ]
    
    for field in move_required_fields:
        assert field in enhanced_move, f"Missing required field: {field}"
    
    # Test holiday move ID prefix
    assert enhanced_move['move_id'].startswith('H'), "Holiday moves should have 'H' prefix"
    
    print("✅ Holiday data structures: PASSED")
    return holiday_period, enhanced_move

def test_move_deduplication_logic():
    """Test move deduplication logic"""
    print("\n🧪 Testing Move Deduplication Logic")
    print("=" * 50)
    
    # Mock moves
    regular_moves = [
        {
            'property': 'SADE',
            'move_id': '1.1',
            'from_unit': 'Cabin 1',
            'to_unit': 'Cabin 2',
            'from_date': '2025-01-20',
            'to_date': '2025-01-25',
            'guest_name': 'John Doe',
            'improvement_score': 0.85
        },
        {
            'property': 'SADE',
            'move_id': '1.2',
            'from_unit': 'Cabin 3',
            'to_unit': 'Cabin 4',
            'from_date': '2025-01-22',
            'to_date': '2025-01-27',
            'guest_name': 'Jane Smith',
            'improvement_score': 0.75
        }
    ]
    
    holiday_moves = [
        {
            'property': 'SADE',
            'move_id': 'H1.1',
            'from_unit': 'Cabin 1',
            'to_unit': 'Cabin 2',
            'from_date': '2025-01-20',
            'to_date': '2025-01-25',
            'guest_name': 'John Doe',
            'improvement_score': 0.85,
            'holiday_period': 'Australia Day 2025',
            'is_holiday_move': True
        },
        {
            'property': 'SADE',
            'move_id': 'H1.2',
            'from_unit': 'Cabin 5',
            'to_unit': 'Cabin 6',
            'from_date': '2025-01-24',
            'to_date': '2025-01-29',
            'guest_name': 'Bob Wilson',
            'improvement_score': 0.90,
            'holiday_period': 'Australia Day 2025',
            'is_holiday_move': True
        }
    ]
    
    # Deduplication function
    def deduplicate_moves(regular_moves: List[Dict], holiday_moves: List[Dict]) -> List[Dict]:
        """Remove duplicate moves between regular and holiday analysis"""
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
    
    # Should have 3 moves (1 duplicate removed)
    assert len(deduplicated_moves) == 3, f"Expected 3 moves, got {len(deduplicated_moves)}"
    
    # Verify unique moves
    move_keys = set()
    for move in deduplicated_moves:
        key = (move['property'], move['from_unit'], move['to_unit'], 
               move['from_date'], move['to_date'])
        assert key not in move_keys, f"Duplicate move found: {key}"
        move_keys.add(key)
    
    print("✅ Move deduplication logic: PASSED")
    return deduplicated_moves

def test_excel_output_structure():
    """Test Excel output structure design"""
    print("\n🧪 Testing Excel Output Structure Design")
    print("=" * 50)
    
    # Mock holiday moves
    holiday_moves = [
        {
            'move_id': 'H1.1',
            'property': 'SADE',
            'from_unit': 'Cabin 1',
            'to_unit': 'Cabin 2',
            'from_date': '2025-01-20',
            'to_date': '2025-01-25',
            'guest_name': 'John Doe',
            'improvement_score': 0.85,
            'holiday_period': 'Australia Day 2025',
            'holiday_type': 'Public Holiday',
            'holiday_importance': 'High',
            'reasoning': 'Creates 3-night contiguous availability'
        }
    ]
    
    # Mock Excel sheet structure
    def create_holiday_sheet_structure(holiday_moves: List[Dict]) -> Dict:
        """Create holiday sheet structure"""
        if not holiday_moves:
            return {}
        
        # Headers
        headers = [
            'Move ID', 'Property', 'From Unit', 'To Unit', 'From Date', 'To Date',
            'Guest Name', 'Improvement Score', 'Holiday Period', 'Holiday Type',
            'Holiday Importance', 'Reasoning'
        ]
        
        # Sheet data
        sheet_data = {
            'sheet_name': 'Holiday Move Suggestions',
            'headers': headers,
            'rows': []
        }
        
        # Add holiday moves data
        for move in holiday_moves:
            row = [
                move.get('move_id', ''),
                move.get('property', ''),
                move.get('from_unit', ''),
                move.get('to_unit', ''),
                move.get('from_date', ''),
                move.get('to_date', ''),
                move.get('guest_name', ''),
                move.get('improvement_score', 0),
                move.get('holiday_period', ''),
                move.get('holiday_type', ''),
                move.get('holiday_importance', ''),
                move.get('reasoning', '')
            ]
            sheet_data['rows'].append(row)
        
        return sheet_data
    
    # Test sheet structure
    sheet_structure = create_holiday_sheet_structure(holiday_moves)
    
    assert sheet_structure['sheet_name'] == 'Holiday Move Suggestions', "Sheet name incorrect"
    assert len(sheet_structure['headers']) == 12, "Should have 12 headers"
    assert len(sheet_structure['rows']) == 1, "Should have 1 row of data"
    
    # Test header structure
    expected_headers = [
        'Move ID', 'Property', 'From Unit', 'To Unit', 'From Date', 'To Date',
        'Guest Name', 'Improvement Score', 'Holiday Period', 'Holiday Type',
        'Holiday Importance', 'Reasoning'
    ]
    
    for expected, actual in zip(expected_headers, sheet_structure['headers']):
        assert expected == actual, f"Header mismatch: expected {expected}, got {actual}"
    
    print("✅ Excel output structure design: PASSED")
    return sheet_structure

def test_email_output_structure():
    """Test email output structure design"""
    print("\n🧪 Testing Email Output Structure Design")
    print("=" * 50)
    
    # Mock holiday moves
    holiday_moves = [
        {
            'move_id': 'H1.1',
            'property': 'SADE',
            'from_unit': 'Cabin 1',
            'to_unit': 'Cabin 2',
            'from_date': '2025-01-20',
            'to_date': '2025-01-25',
            'guest_name': 'John Doe',
            'improvement_score': 0.85,
            'holiday_period': 'Australia Day 2025',
            'holiday_type': 'Public Holiday',
            'holiday_importance': 'High',
            'reasoning': 'Creates 3-night contiguous availability'
        }
    ]
    
    # Mock HTML table generation
    def create_holiday_moves_html_table(holiday_moves: List[Dict]) -> str:
        """Create HTML table for holiday moves"""
        if not holiday_moves:
            return ""
        
        html = "<h3>Holiday Move Suggestions</h3>\n"
        html += "<table border='1' style='border-collapse: collapse; width: 100%;'>\n"
        
        # Headers
        headers = [
            'Move ID', 'Property', 'From Unit', 'To Unit', 'From Date', 'To Date',
            'Guest Name', 'Improvement Score', 'Holiday Period', 'Holiday Type',
            'Holiday Importance', 'Reasoning'
        ]
        
        html += "<tr style='background-color: #f0f0f0;'>\n"
        for header in headers:
            html += f"<th style='padding: 8px; text-align: left;'>{header}</th>\n"
        html += "</tr>\n"
        
        # Data rows
        for move in holiday_moves:
            html += "<tr>\n"
            html += f"<td style='padding: 8px;'>{move.get('move_id', '')}</td>\n"
            html += f"<td style='padding: 8px;'>{move.get('property', '')}</td>\n"
            html += f"<td style='padding: 8px;'>{move.get('from_unit', '')}</td>\n"
            html += f"<td style='padding: 8px;'>{move.get('to_unit', '')}</td>\n"
            html += f"<td style='padding: 8px;'>{move.get('from_date', '')}</td>\n"
            html += f"<td style='padding: 8px;'>{move.get('to_date', '')}</td>\n"
            html += f"<td style='padding: 8px;'>{move.get('guest_name', '')}</td>\n"
            html += f"<td style='padding: 8px;'>{move.get('improvement_score', 0)}</td>\n"
            html += f"<td style='padding: 8px;'>{move.get('holiday_period', '')}</td>\n"
            html += f"<td style='padding: 8px;'>{move.get('holiday_type', '')}</td>\n"
            html += f"<td style='padding: 8px;'>{move.get('holiday_importance', '')}</td>\n"
            html += f"<td style='padding: 8px;'>{move.get('reasoning', '')}</td>\n"
            html += "</tr>\n"
        
        html += "</table>\n"
        return html
    
    # Test HTML table generation
    html_table = create_holiday_moves_html_table(holiday_moves)
    
    # Verify HTML structure
    assert '<h3>Holiday Move Suggestions</h3>' in html_table, "Missing holiday section header"
    assert '<table' in html_table, "Missing table tag"
    assert '<tr>' in html_table, "Missing table row"
    assert '<th style=' in html_table, "Missing table header"
    assert '<td style=' in html_table, "Missing table data"
    
    # Verify content
    assert 'H1.1' in html_table, "Move ID not found in HTML"
    assert 'Australia Day 2025' in html_table, "Holiday period not found in HTML"
    assert 'Public Holiday' in html_table, "Holiday type not found in HTML"
    
    print("✅ Email output structure design: PASSED")
    return html_table

def run_architecture_tests():
    """Run all architecture validation tests"""
    print("🚀 Running Architecture Validation Tests for Step 2")
    print("=" * 60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Run all tests
        test_holiday_client_interface()
        test_state_code_extraction_strategy()
        test_holiday_data_structures()
        test_move_deduplication_logic()
        test_excel_output_structure()
        test_email_output_structure()
        
        print("\n" + "=" * 60)
        print("🎉 ALL ARCHITECTURE TESTS PASSED!")
        print("✅ Architecture design is valid and ready for implementation")
        print("📋 Next: Step 3 - Implement Holiday Client and API Integration")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_architecture_tests()
    sys.exit(0 if success else 1)
