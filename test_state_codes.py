#!/usr/bin/env python3
"""Test script to check state code extraction and population"""

from app.services.rms_service import RMSService
from app.core.database import SessionLocal
from sqlalchemy import text

def test_state_extraction():
    print("=== TESTING STATE CODE EXTRACTION ===")
    
    rms = RMSService()
    
    # Check if method exists
    has_method = hasattr(rms, '_extract_state_code')
    print(f"Has state extraction method: {has_method}")
    
    if has_method:
        # Test with sample data
        test_cases = [
            {'state': 'VIC', 'name': 'Test Property Victoria', 'code': 'VTEST'},
            {'name': 'Queensland Test Property', 'code': 'QTEST'},
            {'name': 'NSW Property', 'code': 'NTEST'},
            {'name': 'Alice Springs', 'code': 'CALI'},  # Should be NT
        ]
        
        for i, test_data in enumerate(test_cases, 1):
            result = rms._extract_state_code(test_data)
            print(f"Test {i}: {test_data} -> {result}")
    
    print("\n=== CHECKING DATABASE ===")
    db = SessionLocal()
    
    # Check current state
    result = db.execute(text("SELECT COUNT(*) FROM properties WHERE state_code IS NOT NULL"))
    count = result.scalar()
    print(f"Properties with state codes: {count}")
    
    # Check total properties
    result = db.execute(text("SELECT COUNT(*) FROM properties"))
    total = result.scalar()
    print(f"Total properties: {total}")
    
    if count == 0 and total > 0:
        print("\n=== TESTING MANUAL REFRESH ===")
        try:
            success = rms.refresh_properties_in_database(db)
            print(f"Manual refresh result: {success}")
            
            # Check again after refresh
            result = db.execute(text("SELECT COUNT(*) FROM properties WHERE state_code IS NOT NULL"))
            new_count = result.scalar()
            print(f"Properties with state codes after refresh: {new_count}")
            
        except Exception as e:
            print(f"Error during refresh: {e}")
    
    db.close()

if __name__ == "__main__":
    test_state_extraction()
