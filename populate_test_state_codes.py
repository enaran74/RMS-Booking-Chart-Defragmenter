#!/usr/bin/env python3
"""Manually populate state codes for testing holiday functionality"""

from app.core.database import SessionLocal
from sqlalchemy import text

def populate_test_state_codes():
    print("=== MANUALLY POPULATING STATE CODES FOR TESTING ===")
    
    db = SessionLocal()
    
    try:
        # Map property code prefixes to states (based on Australian convention)
        state_mappings = [
            ("UPDATE properties SET state_code = 'VIC' WHERE property_code LIKE 'V%'", "Victoria"),
            ("UPDATE properties SET state_code = 'NSW' WHERE property_code LIKE 'N%'", "New South Wales"), 
            ("UPDATE properties SET state_code = 'QLD' WHERE property_code LIKE 'Q%'", "Queensland"),
            ("UPDATE properties SET state_code = 'SA' WHERE property_code LIKE 'S%'", "South Australia"),
            ("UPDATE properties SET state_code = 'TAS' WHERE property_code LIKE 'T%'", "Tasmania"),
            ("UPDATE properties SET state_code = 'WA' WHERE property_code LIKE 'W%'", "Western Australia"),
            ("UPDATE properties SET state_code = 'NT' WHERE property_code LIKE 'C%'", "Northern Territory"),
        ]
        
        total_updated = 0
        for sql, state_name in state_mappings:
            result = db.execute(text(sql))
            count = result.rowcount
            total_updated += count
            print(f"  {state_name}: {count} properties updated")
            
        db.commit()
        print(f"\n✅ Total properties updated with state codes: {total_updated}")
        
        # Verify results
        result = db.execute(text("SELECT state_code, COUNT(*) FROM properties WHERE state_code IS NOT NULL GROUP BY state_code ORDER BY state_code"))
        print("\nFinal breakdown by state:")
        for row in result:
            print(f"  {row[0]}: {row[1]} properties")
            
        # Check total
        result = db.execute(text("SELECT COUNT(*) FROM properties WHERE state_code IS NOT NULL"))
        final_count = result.scalar()
        result = db.execute(text("SELECT COUNT(*) FROM properties"))
        total_count = result.scalar()
        print(f"\nSummary: {final_count}/{total_count} properties now have state codes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_test_state_codes()
