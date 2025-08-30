#!/usr/bin/env python3
from app.services.holiday_client import HolidayClient
from datetime import date

print("=== TESTING HOLIDAY CLIENT ===")

client = HolidayClient()

# Test public holidays for VIC 2025
print("1. Testing public holidays for VIC 2025:")
holidays = client.get_holidays_for_state('VIC', 2025)
print(f"   Found {len(holidays)} public holidays")
for holiday in holidays[:5]:
    print(f"   - {holiday}")

print("\n2. Testing school holidays for VIC:")
school_holidays = client.school_holiday_client.get_school_holidays_for_state('VIC', 2025)
print(f"   Found {len(school_holidays)} school holiday periods")
for holiday in school_holidays[:3]:
    print(f"   - {holiday}")

print("\n3. Testing combined 2-month forward periods:")
combined = client.get_combined_holiday_periods_2month_forward('VIC', date.today())
print(f"   Found {len(combined)} combined holiday periods")
for period in combined[:3]:
    print(f"   - {period['name']} ({period['type']}) from {period['start_date']} to {period['end_date']}")

print("\n=== TEST COMPLETE ===")
