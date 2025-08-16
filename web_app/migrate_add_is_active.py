#!/usr/bin/env python3
"""
Migration script to add is_active column to properties table
Run this script to update the database schema
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from app.core.database import engine, Base
from app.models.property import Property
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

def migrate_properties_table():
    """Add is_active column to properties table"""
    print("🔄 Starting properties table migration...")
    
    try:
        # Create a session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if is_active column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'properties' AND column_name = 'is_active'
        """))
        
        if result.fetchone():
            print("✅ is_active column already exists in properties table")
            return True
        
        # Add is_active column with default value True
        print("📝 Adding is_active column to properties table...")
        db.execute(text("""
            ALTER TABLE properties 
            ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE
        """))
        
        # Update existing properties to be active by default
        print("🔄 Updating existing properties to be active...")
        db.execute(text("""
            UPDATE properties 
            SET is_active = TRUE 
            WHERE is_active IS NULL
        """))
        
        # Commit the changes
        db.commit()
        print("✅ Successfully added is_active column to properties table")
        
        # Verify the migration
        properties = db.query(Property).all()
        print(f"📊 Properties table now has {len(properties)} properties with is_active field")
        
        # Show a few examples
        for i, prop in enumerate(properties[:5]):
            print(f"   {i+1}. {prop.property_code} - {prop.property_name} (Active: {prop.is_active})")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Properties Table Migration Script")
    print("=" * 50)
    
    success = migrate_properties_table()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("The properties table now includes the is_active field.")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)
