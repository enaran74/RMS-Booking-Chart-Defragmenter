#!/usr/bin/env python3
from app.core.database import SessionLocal
from sqlalchemy import text

print("=== CHECKING STATE CODES ===")
db = SessionLocal()

# Check if we have any state codes now
result = db.execute(text("SELECT COUNT(*) FROM properties WHERE state_code IS NOT NULL"))
count = result.scalar()
print(f"Properties with state codes: {count}")

# Check total properties  
result = db.execute(text("SELECT COUNT(*) FROM properties"))
total = result.scalar()
print(f"Total properties: {total}")

if count == 0:
    print("\nNo state codes found yet. You may need to refresh properties from the web interface.")
else:
    print(f"\n✅ SUCCESS! {count} properties have state codes!")
    
    # Show breakdown by state
    result = db.execute(text("SELECT state_code, COUNT(*) FROM properties WHERE state_code IS NOT NULL GROUP BY state_code ORDER BY state_code"))
    print("\nBreakdown by state:")
    for row in result:
        print(f"  {row[0]}: {row[1]} properties")

db.close()
