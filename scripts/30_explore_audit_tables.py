import pandas as pd
import wrds

print("=" * 60)
print("EXPLORING AUDIT ANALYTICS TABLE STRUCTURE")
print("=" * 60)

# Connect to WRDS
db = wrds.Connection()
print("✓ Connected to WRDS\n")

# ============================================================
# EXPLORE SOX 404 TABLE
# ============================================================

print("=" * 60)
print("1. SOX 404 INTERNAL CONTROLS TABLE")
print("=" * 60)

try:
    # Get sample data to see column names
    sox_sample = db.raw_sql("""
        SELECT * 
        FROM audit.feed11_sox_404_internal_controls 
        LIMIT 5
    """)
    
    print(f"\n✓ Table exists with {len(sox_sample)} sample rows")
    print(f"\nColumn names:")
    for i, col in enumerate(sox_sample.columns, 1):
        print(f"  {i}. {col}")
    
    print(f"\nSample data:")
    print(sox_sample.head(2).to_string())
    
    # Save sample
    sox_sample.to_csv('Data/audit_analytics/sox_sample.csv', index=False)
    
except Exception as e:
    print(f"✗ Error: {e}")

# ============================================================
# EXPLORE RESTATEMENTS TABLE
# ============================================================

print("\n" + "=" * 60)
print("2. FINANCIAL RESTATEMENTS TABLE")
print("=" * 60)

try:
    # Get sample data
    restate_sample = db.raw_sql("""
        SELECT * 
        FROM audit.feed39_financial_restatements 
        LIMIT 5
    """)
    
    print(f"\n✓ Table exists with {len(restate_sample)} sample rows")
    print(f"\nColumn names:")
    for i, col in enumerate(restate_sample.columns, 1):
        print(f"  {i}. {col}")
    
    print(f"\nSample data:")
    print(restate_sample.head(2).to_string())
    
    # Save sample
    restate_sample.to_csv('Data/audit_analytics/restatements_sample.csv', index=False)
    
except Exception as e:
    print(f"✗ Error: {e}")

# ============================================================
# TEST WITH ONE CIK
# ============================================================

print("\n" + "=" * 60)
print("3. TEST QUERY WITH SAMPLE CIK")
print("=" * 60)

# Use Microsoft's CIK as test
test_cik = 789019  # Microsoft

print(f"\nTesting with CIK: {test_cik} (Microsoft)")

# Test SOX
try:
    print("\nSOX 404 data for this company:")
    sox_test = db.raw_sql(f"""
        SELECT * 
        FROM audit.feed11_sox_404_internal_controls 
        WHERE company_fkey = {test_cik}
        LIMIT 5
    """)
    
    if len(sox_test) > 0:
        print(f"  ✓ Found {len(sox_test)} SOX records")
        print(sox_test.to_string())
    else:
        print("  ✗ No SOX records for this company")
        
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test Restatements
try:
    print("\nRestatement data for this company:")
    restate_test = db.raw_sql(f"""
        SELECT * 
        FROM audit.feed39_financial_restatements 
        WHERE company_fkey = {test_cik}
        LIMIT 5
    """)
    
    if len(restate_test) > 0:
        print(f"  ✓ Found {len(restate_test)} restatement records")
        print(restate_test.to_string())
    else:
        print("  ✗ No restatement records for this company")
        
except Exception as e:
    print(f"  ✗ Error: {e}")

db.close()
print("\n✓ WRDS connection closed")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("\nCheck the output above for:")
print("  1. Actual column names in each table")
print("  2. Whether data exists for your companies")
print("  3. Date column names to use for filtering")