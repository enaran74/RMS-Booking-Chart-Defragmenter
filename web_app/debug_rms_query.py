#!/usr/bin/env python3
"""
Debug script to query RMS API directly with the same parameters as chart service
This will help us see exactly what reservations are being returned
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RMSDebugClient:
    def __init__(self):
        self.base_url = "https://restapi12.rmscloud.com"
        self.session = requests.Session()
        self.token = None
        
        # Get credentials from environment
        self.agent_id = os.getenv('AGENT_ID')
        self.agent_password = os.getenv('AGENT_PASSWORD')
        self.client_id = os.getenv('CLIENT_ID')
        self.client_password = os.getenv('CLIENT_PASSWORD')
        
        # Same date constraints as lightweight RMS client
        today = datetime.now().date()
        self.constraint_start_date = today
        self.constraint_end_date = today + timedelta(days=31)
        
        print(f"🔍 RMS Debug Client initialized")
        print(f"📅 Date range: {self.constraint_start_date} to {self.constraint_end_date}")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"👤 Agent ID: {self.agent_id}")
        print(f"🏢 Client ID: {self.client_id}")
        
    def authenticate(self):
        """Authenticate with RMS API"""
        print(f"\n🔐 Authenticating with RMS API...")
        
        auth_payload = {
            "agentId": self.agent_id,
            "agentPassword": self.agent_password,
            "clientId": self.client_id,
            "clientPassword": self.client_password
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/tokens",
                json=auth_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"🌐 Auth response status: {response.status_code}")
            
            if response.status_code == 200:
                self.token = response.json().get('token')
                print(f"✅ Authentication successful")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                return True
            else:
                print(f"❌ Authentication failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Auth error: {str(e)}")
            return False
    
    def get_property_id_for_code(self, property_code: str):
        """Get RMS property ID for a property code"""
        print(f"\n🏨 Getting property ID for code: {property_code}")
        
        try:
            response = self.session.get(f"{self.base_url}/properties")
            
            if response.status_code == 200:
                properties = response.json()
                print(f"📋 Found {len(properties)} total properties")
                
                for prop in properties:
                    if prop.get('propertyCode', '').upper() == property_code.upper():
                        property_id = prop.get('id')
                        print(f"✅ Found property: {prop.get('name')} (ID: {property_id})")
                        return property_id
                        
                print(f"❌ Property {property_code} not found")
                return None
            else:
                print(f"❌ Failed to fetch properties: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching properties: {str(e)}")
            return None
    
    def get_property_categories(self, property_id: int):
        """Get categories for a property"""
        print(f"\n📂 Getting categories for property {property_id}")
        
        try:
            response = self.session.get(f"{self.base_url}/properties/{property_id}/categories")
            
            if response.status_code == 200:
                categories = response.json()
                print(f"📋 Found {len(categories)} categories")
                for cat in categories[:5]:  # Show first 5
                    print(f"  - {cat.get('name')} (ID: {cat.get('id')})")
                if len(categories) > 5:
                    print(f"  ... and {len(categories) - 5} more")
                return categories
            else:
                print(f"❌ Failed to fetch categories: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching categories: {str(e)}")
            return []
    
    def debug_reservations_query(self, property_code: str):
        """Query reservations with exact same parameters as chart service"""
        print(f"\n🔍 DEBUG: Querying reservations for {property_code} with chart service parameters")
        
        # Get property ID
        property_id = self.get_property_id_for_code(property_code)
        if not property_id:
            return
        
        # Get categories
        categories = self.get_property_categories(property_id)
        if not categories:
            print("❌ No categories found - cannot query reservations")
            return
        
        category_ids = [cat['id'] for cat in categories]
        
        # Build exact same payload as lightweight RMS client
        search_payload = {
            "propertyIds": [property_id],
            "categoryIds": category_ids,
            "arriveFrom": "2000-01-01 00:00:00",
            "arriveTo": f"{self.constraint_end_date} 23:59:59",
            "departFrom": f"{self.constraint_start_date} 00:00:00",
            "departTo": "2050-12-31 23:59:59",
            "listOfStatus": [
                "unconfirmed", "confirmed", "arrived", "maintenance", 
                "quote", "ownerOccupied", "pencil", "departed"
            ],
            "includeGroupMasterReservations": "ExcludeGroupMasters",
            "includeInterconnecterSiblings": False,
            "includeRoomMoveHeaders": False,
            "limitProjectedRevenueToDateRange": False
        }
        
        params = {
            'limit': 2000,
            'modelType': 'full',
            'offset': 0
        }
        
        print(f"\n📋 Query Parameters:")
        print(f"  Property ID: {property_id}")
        print(f"  Categories: {len(category_ids)} category IDs")
        print(f"  Arrive From: 2000-01-01 00:00:00")
        print(f"  Arrive To: {self.constraint_end_date} 23:59:59")
        print(f"  Depart From: {self.constraint_start_date} 00:00:00")
        print(f"  Depart To: 2050-12-31 23:59:59")
        print(f"  Status filters: {search_payload['listOfStatus']}")
        
        try:
            print(f"\n🌐 Making API call to /reservations/search...")
            response = self.session.post(
                f"{self.base_url}/reservations/search",
                json=search_payload,
                params=params,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                reservations = response.json()
                print(f"✅ Found {len(reservations)} reservations")
                
                # Look for specific guests mentioned in the issue
                target_guests = ['Coombs', 'JIANMIN', 'Trembath', 'Anderson', 'Murray', 'Peterson', 'Brown']
                
                print(f"\n🔍 Looking for specific guests: {target_guests}")
                found_guests = {}
                
                for res in reservations:
                    guest_name = res.get('guestSurname', '').strip()
                    if guest_name in target_guests:
                        if guest_name not in found_guests:
                            found_guests[guest_name] = []
                        
                        found_guests[guest_name].append({
                            'res_no': res.get('reservationNumber'),
                            'arrive': res.get('arrive'),
                            'depart': res.get('depart'),
                            'unit': res.get('unitName'),
                            'status': res.get('status'),
                            'category': res.get('categoryName')
                        })
                
                print(f"\n📋 Found guest reservations:")
                for guest, reservations_list in found_guests.items():
                    print(f"\n👤 {guest} ({len(reservations_list)} reservation(s)):")
                    for i, res in enumerate(reservations_list):
                        print(f"    {i+1}. Res#{res['res_no']} | {res['arrive']} → {res['depart']} | {res['unit']} | {res['status']}")
                
                if not found_guests:
                    print(f"❌ None of the target guests found in API response")
                    print(f"\n📋 Sample of returned guests (first 10):")
                    for i, res in enumerate(reservations[:10]):
                        print(f"  {i+1}. {res.get('guestSurname', 'Unknown')} | Res#{res.get('reservationNumber')} | {res.get('arrive')} → {res.get('depart')} | {res.get('unitName')}")
                
                return reservations
                
            else:
                print(f"❌ API call failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error querying reservations: {str(e)}")
            return None

def main():
    """Main debug function"""
    print("🔍 RMS API Direct Query Debug Tool")
    print("=" * 50)
    
    client = RMSDebugClient()
    
    # Authenticate
    if not client.authenticate():
        print("❌ Authentication failed - cannot proceed")
        return
    
    # Debug reservations for CALI (the property we're having issues with)
    property_code = "CALI"
    reservations = client.debug_reservations_query(property_code)
    
    if reservations:
        print(f"\n✅ Successfully retrieved {len(reservations)} reservations from RMS API")
        print(f"This matches what our chart service should be getting.")
    else:
        print(f"\n❌ Failed to retrieve reservations - this explains the missing data")

if __name__ == "__main__":
    main()
