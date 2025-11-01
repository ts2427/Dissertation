import pandas as pd
import wrds
from datetime import datetime

print("=" * 60)
print("DOWNLOADING AUDIT ANALYTICS DATA (CORRECTED)")
print("=" * 60)

# Load breach dataset
breach_df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')
print(f"\n✓ Loaded {len(breach_df)} breach records")

# Get unique CIK codes and date range
ciks = breach_df['CIK CODE'].dropna().unique().tolist()
min_date = breach_df['breach_date'].min() - pd.DateOffset(years=2)
max_date = breach_df['breach_date'].max()

print(f"  Unique CIKs: {len(ciks)}")
print(f"  Date range: {min_date.date()} to {max_date.date()}")

# Connect to WRDS
print("\n[1/3] Connecting to WRDS...")
db = wrds.Connection()
print("✓ Connected")

# Create CIK list for SQL
cik_list = ','.join([str(int(c)) for c in ciks])

import os
os.makedirs('Data/audit_analytics', exist_ok=True)

# ============================================================
# 1. SOX 404 INTERNAL CONTROLS
# ============================================================

print("\n[2/3] Downloading SOX 404 internal control data...")

# CORRECT TABLE: auditnonreli.sox_404
sox_query = f"""
    SELECT company_fkey, fiscal_year_end, file_date,
           auditor_fkey, is404, ic_is_effective,
           material_weakness_disclosed
    FROM audit.auditopinion
    WHERE company_fkey IN ({cik_list})
    AND fiscal_year_end >= '{min_date.strftime('%Y-%m-%d')}'
    AND fiscal_year_end <= '{max_date.strftime('%Y-%m-%d')}'
"""

try:
    print("  Querying SOX 404 data...")
    sox_data = db.raw_sql(sox_query)
    
    if len(sox_data) > 0:
        sox_data.to_csv('Data/audit_analytics/sox_404_data.csv', index=False)
        print(f"✓ Downloaded {len(sox_data):,} SOX 404 records")
        
        # Show summary
        print(f"\n  Material weaknesses disclosed: {sox_data['material_weakness_disclosed'].sum()}")
        print(f"  Effective internal controls: {sox_data['ic_is_effective'].sum()}")
        
        # Show sample
        print("\n  Sample records:")
        print(sox_data.head(3))
    else:
        print("✗ No SOX 404 data found")
        
except Exception as e:
    print(f"✗ SOX 404 download failed: {e}")
    print("\nTrying alternative table paths...")
    
    # Try alternative table names
    alternative_tables = [
        'audit.soxcontrol',
        'audit.sox404',
        'auditnonreli.sox_404'
    ]
    
    for table in alternative_tables:
        try:
            print(f"  Trying: {table}")
            test_query = f"SELECT * FROM {table} LIMIT 5"
            test_data = db.raw_sql(test_query)
            print(f"  ✓ Found! Table {table} exists")
            print(f"    Columns: {test_data.columns.tolist()}")
            break
        except:
            continue

# ============================================================
# 2. FINANCIAL RESTATEMENTS
# ============================================================

print("\n[3/3] Downloading financial restatement data...")

# CORRECT TABLE: auditnonreli
restatement_query = f"""
    SELECT company_fkey, file_date, 
           res_begin_date, res_end_date, res_notif_key,
           res_accounting, res_adverse, res_fraud, 
           res_sec_invest, restatement_key
    FROM audit.auditnonreli
    WHERE company_fkey IN ({cik_list})
    AND res_begin_date >= '{min_date.strftime('%Y-%m-%d')}'
"""

try:
    print("  Querying restatement data...")
    restatement_data = db.raw_sql(restatement_query)
    
    if len(restatement_data) > 0:
        restatement_data.to_csv('Data/audit_analytics/restatements.csv', index=False)
        print(f"✓ Downloaded {len(restatement_data):,} restatement records")
        
        # Show summary
        print(f"\n  Accounting restatements: {restatement_data['res_accounting'].sum()}")
        print(f"  Fraud-related: {restatement_data['res_fraud'].sum()}")
        print(f"  SEC investigations: {restatement_data['res_sec_invest'].sum()}")
        
        # Show sample
        print("\n  Sample records:")
        print(restatement_data.head(3))
    else:
        print("✗ No restatement data found")
        
except Exception as e:
    print(f"✗ Restatement download failed: {e}")
    print("\nTrying to list available audit tables...")
    
    try:
        tables = db.list_tables(library='audit')
        print(f"Available audit tables: {tables}")
    except:
        print("Could not list tables")

# Close connection
db.close()
print("\n✓ WRDS connection closed")

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("DOWNLOAD SUMMARY")
print("=" * 60)

if 'sox_data' in locals() and len(sox_data) > 0:
    print(f"\n✓ SOX 404 Data: {len(sox_data)} records")
else:
    print(f"\n✗ SOX 404 Data: No records downloaded")

if 'restatement_data' in locals() and len(restatement_data) > 0:
    print(f"✓ Restatement Data: {len(restatement_data)} records")
else:
    print(f"✗ Restatement Data: No records downloaded")

print("\n" + "=" * 60)
print("NEXT STEPS")
print("=" * 60)

print("\nIf downloads succeeded:")
print("  1. Run: python scripts/29_merge_audit_data.py")
print("  2. This will add SOX/restatement flags to your breach data")

print("\nIf downloads failed:")
print("  1. Check the 'Available audit tables' output above")
print("  2. Look for tables with 'sox' or 'restate' in the name")
print("  3. Update queries with correct table names")