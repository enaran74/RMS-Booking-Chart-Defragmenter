#!/usr/bin/env python3
"""Add holiday integration schema to existing database"""

from app.core.database import SessionLocal
from sqlalchemy import text

def add_holiday_schema():
    print("=== ADDING HOLIDAY INTEGRATION SCHEMA ===")
    
    db = SessionLocal()
    
    try:
        # Add state_code column to properties table
        print("Adding state_code column to properties...")
        db.execute(text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS state_code VARCHAR(10)"))
        
        # Add holiday columns to defrag_moves table
        print("Adding holiday columns to defrag_moves...")
        db.execute(text("ALTER TABLE defrag_moves ADD COLUMN IF NOT EXISTS is_holiday_move BOOLEAN DEFAULT FALSE"))
        db.execute(text("ALTER TABLE defrag_moves ADD COLUMN IF NOT EXISTS holiday_period_name VARCHAR(255)"))
        db.execute(text("ALTER TABLE defrag_moves ADD COLUMN IF NOT EXISTS holiday_type VARCHAR(50)"))
        db.execute(text("ALTER TABLE defrag_moves ADD COLUMN IF NOT EXISTS holiday_importance VARCHAR(20)"))
        
        # Add indexes for performance
        print("Adding indexes...")
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_properties_state_code ON properties(state_code)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_defrag_moves_holiday ON defrag_moves(is_holiday_move)"))
        except Exception as e:
            print(f"Index creation (may already exist): {e}")
        
        db.commit()
        print("✅ Schema update completed successfully!")
        
        # Verify the changes
        print("\n=== VERIFICATION ===")
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'properties' AND column_name = 'state_code'"))
        if result.fetchone():
            print("✅ state_code column added to properties")
        else:
            print("❌ state_code column not found")
            
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'defrag_moves' AND column_name = 'is_holiday_move'"))
        if result.fetchone():
            print("✅ holiday columns added to defrag_moves")
        else:
            print("❌ holiday columns not found")
            
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_holiday_schema()
