import pandas as pd
import wrds
from datetime import datetime

print("=" * 60)
print("DOWNLOADING AUDIT ANALYTICS DATA (CORRECT TABLES)")
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
# 1. SOX 404 INTERNAL CONTROLS - CORRECT TABLE
# ============================================================

print("\n[2/3] Downloading SOX 404 internal control data...")

sox_query = f"""
    SELECT company_fkey, fiscal_year_end, file_date,
           auditor_fkey, is404, ic_is_effective,
           material_weakness_key, going_concern
    FROM audit.feed11_sox_404_internal_controls
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
        if 'material_weakness_key' in sox_data.columns:
            print(f"\n  Records with material weakness: {sox_data['material_weakness_key'].notna().sum()}")
        if 'ic_is_effective' in sox_data.columns:
            print(f"  Effective internal controls: {sox_data['ic_is_effective'].sum()}")
        if 'going_concern' in sox_data.columns:
            print(f"  Going concern issues: {sox_data['going_concern'].sum()}")
        
        # Show sample
        print("\n  Sample records:")
        print(sox_data.head(3).to_string())
        
        # Show column names
        print(f"\n  Columns: {sox_data.columns.tolist()}")
    else:
        print("✗ No SOX 404 data found for these CIKs")
        
except Exception as e:
    print(f"✗ SOX 404 download failed: {e}")

# ============================================================
# 2. FINANCIAL RESTATEMENTS - CORRECT TABLE
# ============================================================

print("\n[3/3] Downloading financial restatement data...")

restatement_query = f"""
    SELECT company_fkey, file_date, 
           res_begin_date, res_end_date, res_notif_key,
           res_accounting, res_adverse, res_fraud, 
           res_sec_invest, restatement_key
    FROM audit.feed39_financial_restatements
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
        if 'res_accounting' in restatement_data.columns:
            print(f"\n  Accounting restatements: {restatement_data['res_accounting'].sum()}")
        if 'res_fraud' in restatement_data.columns:
            print(f"  Fraud-related: {restatement_data['res_fraud'].sum()}")
        if 'res_sec_invest' in restatement_data.columns:
            print(f"  SEC investigations: {restatement_data['res_sec_invest'].sum()}")
        
        # Show sample
        print("\n  Sample records:")
        print(restatement_data.head(3).to_string())
        
        # Show column names
        print(f"\n  Columns: {restatement_data.columns.tolist()}")
    else:
        print("✗ No restatement data found for these CIKs")
        
except Exception as e:
    print(f"✗ Restatement download failed: {e}")

# Close connection
db.close()
print("\n✓ WRDS connection closed")

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("DOWNLOAD SUMMARY")
print("=" * 60)

sox_success = 'sox_data' in locals() and len(sox_data) > 0
restate_success = 'restatement_data' in locals() and len(restatement_data) > 0

if sox_success:
    print(f"\n✓ SOX 404 Data: {len(sox_data)} records")
    print(f"  Unique companies: {sox_data['company_fkey'].nunique()}")
    print(f"  Date range: {sox_data['fiscal_year_end'].min()} to {sox_data['fiscal_year_end'].max()}")
else:
    print(f"\n✗ SOX 404 Data: No records downloaded")

if restate_success:
    print(f"\n✓ Restatement Data: {len(restatement_data)} records")
    print(f"  Unique companies: {restatement_data['company_fkey'].nunique()}")
    print(f"  Date range: {restatement_data['res_begin_date'].min()} to {restatement_data['res_begin_date'].max()}")
else:
    print(f"\n✗ Restatement Data: No records downloaded")

if sox_success or restate_success:
    print("\n" + "=" * 60)
    print("✓ SUCCESS - DATA DOWNLOADED")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run: python scripts/30_merge_audit_data.py")
    print("  2. This will create governance quality variables")
    print("  3. Re-run Essay 3 analysis with governance controls")
else:
    print("\n" + "=" * 60)
    print("⚠ NO DATA FOUND")
    print("=" * 60)
    print("\nPossible reasons:")
    print("  1. Your companies may not have SOX 404 or restatement data")
    print("  2. CIK matching might be the issue")
    print("  3. Date range might be too restrictive")
    
    print("\nTroubleshooting:")
    print("  Try querying without CIK filter to see if data exists:")
    print("  SELECT * FROM audit.feed11_sox_404_internal_controls LIMIT 10")