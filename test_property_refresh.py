#!/usr/bin/env python3
"""Test property refresh and state extraction"""

from app.core.database import SessionLocal
from app.services.rms_service import RMSService
from sqlalchemy import text

def test_property_refresh():
    print("=== TESTING PROPERTY REFRESH AND STATE EXTRACTION ===")
    
    db = SessionLocal()
    rms_service = RMSService()
    
    try:
        # Test if state extraction method exists
        has_method = hasattr(rms_service, '_extract_state_code')
        print(f"Has state extraction method: {has_method}")
        
        if has_method:
            # Test with sample data
            test_cases = [
                {'state': 'VIC', 'name': 'Victoria Test', 'code': 'VTEST'},
                {'name': 'Queensland Property', 'code': 'QTEST'},
                {'name': 'Alice Springs', 'code': 'CALI'},  # Should extract NT from name
            ]
            
            print("\nTesting state extraction with sample data:")
            for i, test_data in enumerate(test_cases, 1):
                result = rms_service._extract_state_code(test_data)
                print(f"  Test {i}: {test_data['name']} -> {result}")
        
        # Check current properties before refresh
        result = db.execute(text("SELECT COUNT(*) FROM properties"))
        total_before = result.scalar()
        print(f"\nProperties before refresh: {total_before}")
        
        # Try manual refresh
        print("\nAttempting manual property refresh...")
        try:
            success = rms_service.refresh_properties_in_database(db)
            print(f"Refresh result: {success}")
            
            # Check after refresh
            result = db.execute(text("SELECT COUNT(*) FROM properties WHERE state_code IS NOT NULL"))
            state_count = result.scalar()
            print(f"Properties with state codes after refresh: {state_count}")
            
            if state_count > 0:
                print("\n✅ SUCCESS! State codes populated:")
                result = db.execute(text("SELECT state_code, COUNT(*) FROM properties WHERE state_code IS NOT NULL GROUP BY state_code"))
                for row in result:
                    print(f"  {row[0]}: {row[1]} properties")
            else:
                print("\n❌ No state codes populated")
                # Check a sample property to see what data we have
                result = db.execute(text("SELECT property_code, property_name FROM properties LIMIT 3"))
                print("Sample properties (might help debug):")
                for row in result:
                    print(f"  {row[0]}: {row[1]}")
                    
        except Exception as refresh_error:
            print(f"❌ Refresh failed: {refresh_error}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_property_refresh()
