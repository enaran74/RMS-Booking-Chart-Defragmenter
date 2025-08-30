#!/usr/bin/env python3
try:
    from app.services.holiday_client import HolidayClient
    print("SUCCESS: HolidayClient import")
    client = HolidayClient()
    print("SUCCESS: HolidayClient creation")
except Exception as e:
    print(f"ERROR: {e}")
