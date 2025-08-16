#!/usr/bin/env python3
"""
Test script for RMS API integration
Run this to verify that we can connect to RMS API and fetch properties
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from app.services.rms_service import rms_service
from app.core.database import engine, Base, get_db
from app.models.property import Property
from sqlalchemy.orm import sessionmaker

def test_rms_connection():
    """Test RMS API connection and authentication"""
    print("🔐 Testing RMS API Connection...")
    print("=" * 50)
    
    # Test authentication
    if rms_service.authenticate():
        print("✅ RMS API authentication successful!")
        print(f"🔑 Token: {rms_service.token[:20]}...")
        print(f"⏰ Expires: {rms_service.token_expiry}")
    else:
        print("❌ RMS API authentication failed!")
        return False
    
    # Test property fetching
    print("\n📡 Testing Property Fetching...")
    print("=" * 50)
    
    properties = rms_service.fetch_properties()
    if properties:
        print(f"✅ Successfully fetched {len(properties)} properties from RMS API")
        
        # Show first few properties as examples
        print("\n📋 Sample Properties:")
        for i, prop in enumerate(properties[:5]):
            property_info = rms_service._extract_property_info(prop)
            if property_info:
                print(f"   {i+1}. Code: '{property_info['code']}' | Name: '{property_info['name']}'")
            else:
                print(f"   {i+1}. Could not extract info from: {prop}")
        
        if len(properties) > 5:
            print(f"   ... and {len(properties) - 5} more properties")
    else:
        print("❌ Failed to fetch properties from RMS API")
        return False
    
    return True

def test_database_integration():
    """Test database integration for properties"""
    print("\n🗄️  Testing Database Integration...")
    print("=" * 50)
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
        
        # Create a session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Test property refresh
            print("🔄 Testing property refresh in database...")
            success = rms_service.refresh_properties_in_database(db)
            
            if success:
                print("✅ Properties successfully refreshed in database")
                
                # Get properties from database
                properties = rms_service.get_properties_from_database(db)
                print(f"📊 Retrieved {len(properties)} properties from database")
                
                # Show some examples
                print("\n📋 Database Properties:")
                for i, prop in enumerate(properties[:5]):
                    print(f"   {i+1}. ID: {prop.id} | Code: '{prop.property_code}' | Name: '{prop.property_name}'")
                
                if len(properties) > 5:
                    print(f"   ... and {len(properties) - 5} more properties")
                    
            else:
                print("❌ Failed to refresh properties in database")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🚀 RMS API Integration Test")
    print("=" * 60)
    
    # Test RMS connection
    if not test_rms_connection():
        print("\n❌ RMS API test failed!")
        return
    
    # Test database integration
    if not test_database_integration():
        print("\n❌ Database integration test failed!")
        return
    
    print("\n🎉 All tests passed! RMS integration is working correctly.")
    print("\n📝 Next steps:")
    print("   1. Deploy the web app to your VPS")
    print("   2. Test the /api/v1/properties endpoint")
    print("   3. Verify properties are loaded in the web interface")

if __name__ == "__main__":
    main()
