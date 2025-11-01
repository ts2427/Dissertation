import pandas as pd
import wrds

print("=" * 60)
print("DOWNLOADING AUDIT ANALYTICS DATA (FINAL VERSION)")
print("=" * 60)

# Load breach dataset
breach_df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')
print(f"\n✓ Loaded {len(breach_df)} breach records")

# Get unique CIK codes
ciks = breach_df['CIK CODE'].dropna().unique().tolist()
min_date = breach_df['breach_date'].min() - pd.DateOffset(years=2)
max_date = breach_df['breach_date'].max()

print(f"  Unique CIKs: {len(ciks)}")
print(f"  Date range: {min_date.date()} to {max_date.date()}")

# Connect to WRDS
db = wrds.Connection()
print("✓ Connected to WRDS\n")

import os
os.makedirs('Data/audit_analytics', exist_ok=True)

# Create CIK list for SQL - CAST AS TEXT
cik_list = ','.join([f"'{int(c)}'" for c in ciks])  # Wrap in quotes for string comparison

# ============================================================
# 1. SOX 404 INTERNAL CONTROLS
# ============================================================

print("=" * 60)
print("1. SOX 404 INTERNAL CONTROLS")
print("=" * 60)

sox_query = f"""
    SELECT company_fkey, 
           fye_ic_op,
           ic_is_effective,
           count_weak,
           file_date,
           auditor_fkey,
           restatement
    FROM audit.feed11_sox_404_internal_controls
    WHERE company_fkey IN ({cik_list})
    AND fye_ic_op >= '{min_date.strftime('%Y-%m-%d')}'
    AND fye_ic_op <= '{max_date.strftime('%Y-%m-%d')}'
"""

try:
    print("  Querying SOX 404 data...")
    sox_data = db.raw_sql(sox_query)
    
    if len(sox_data) > 0:
        # Convert company_fkey to integer for merging
        sox_data['company_fkey'] = sox_data['company_fkey'].astype(int)
        
        sox_data.to_csv('Data/audit_analytics/sox_404_data.csv', index=False)
        print(f"✓ Downloaded {len(sox_data):,} SOX 404 records")
        print(f"  Unique companies: {sox_data['company_fkey'].nunique()}")
        print(f"  Date range: {sox_data['fye_ic_op'].min()} to {sox_data['fye_ic_op'].max()}")
        
        # Summary stats
        print(f"\n  Summary:")
        print(f"    Effective internal controls: {sox_data['ic_is_effective'].sum()}")
        print(f"    Material weaknesses (count_weak > 0): {(sox_data['count_weak'] > 0).sum()}")
        print(f"    Restatements: {sox_data['restatement'].sum()}")
        
        print(f"\n  Sample records:")
        print(sox_data[['company_fkey', 'fye_ic_op', 'ic_is_effective', 'count_weak']].head())
    else:
        print("✗ No SOX 404 data found for these CIKs")
        
except Exception as e:
    print(f"✗ SOX 404 download failed: {e}")

# ============================================================
# 2. FINANCIAL RESTATEMENTS
# ============================================================

print("\n" + "=" * 60)
print("2. FINANCIAL RESTATEMENTS")
print("=" * 60)

restatement_query = f"""
    SELECT company_fkey, 
           file_date,
           res_begin_date, 
           res_end_date,
           res_accounting, 
           res_fraud,
           res_adverse,
           res_sec_investigation,
           restatement_notification_key
    FROM audit.feed39_financial_restatements
    WHERE company_fkey IN ({cik_list})
    AND res_begin_date >= '{min_date.strftime('%Y-%m-%d')}'
"""

try:
    print("  Querying restatement data...")
    restatement_data = db.raw_sql(restatement_query)
    
    if len(restatement_data) > 0:
        # Convert company_fkey to integer for merging
        restatement_data['company_fkey'] = restatement_data['company_fkey'].astype(int)
        
        restatement_data.to_csv('Data/audit_analytics/restatements.csv', index=False)
        print(f"✓ Downloaded {len(restatement_data):,} restatement records")
        print(f"  Unique companies: {restatement_data['company_fkey'].nunique()}")
        print(f"  Date range: {restatement_data['res_begin_date'].min()} to {restatement_data['res_end_date'].max()}")
        
        # Summary stats
        print(f"\n  Summary:")
        print(f"    Accounting restatements: {restatement_data['res_accounting'].sum()}")
        print(f"    Fraud-related: {restatement_data['res_fraud'].sum()}")
        print(f"    Adverse: {restatement_data['res_adverse'].sum()}")
        print(f"    SEC investigations: {restatement_data['res_sec_investigation'].sum()}")
        
        print(f"\n  Sample records:")
        print(restatement_data[['company_fkey', 'res_begin_date', 'res_accounting', 'res_fraud']].head())
    else:
        print("✗ No restatement data found for these CIKs")
        
except Exception as e:
    print(f"✗ Restatement download failed: {e}")

db.close()
print("\n✓ WRDS connection closed")

# ============================================================
# SUMMARY & NEXT STEPS
# ============================================================

print("\n" + "=" * 60)
print("DOWNLOAD SUMMARY")
print("=" * 60)

sox_success = 'sox_data' in locals() and len(sox_data) > 0
restate_success = 'restatement_data' in locals() and len(restatement_data) > 0

if sox_success:
    print(f"\n✓ SOX 404: {len(sox_data)} records covering {sox_data['company_fkey'].nunique()} companies")
else:
    print(f"\n✗ SOX 404: No data")

if restate_success:
    print(f"✓ Restatements: {len(restatement_data)} records covering {restatement_data['company_fkey'].nunique()} companies")
else:
    print(f"✗ Restatements: No data")

if sox_success or restate_success:
    print("\n" + "=" * 60)
    print("✓ SUCCESS - READY TO MERGE")
    print("=" * 60)
    print("\nNext step:")
    print("  Run: python scripts/32_merge_audit_data.py")
    print("  This will create governance variables for Essay 3")
else:
    print("\n⚠ Your companies may not have Audit Analytics data")
    print("  This is common - many companies don't have SOX weaknesses or restatements")
    print("  You can still complete Essay 3 using firm size as governance proxy")