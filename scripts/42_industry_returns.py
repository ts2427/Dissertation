import pandas as pd
import numpy as np
import wrds

print("=" * 60)
print("SCRIPT 2: INDUSTRY-ADJUSTED RETURNS")
print("=" * 60)

# Load breach data
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')
print(f"\n✓ Loaded {len(df)} breach records")

# Filter to those with CRSP data
analysis_df = df[df['has_crsp_data'] == True].copy()
print(f"✓ Records with CRSP data: {len(analysis_df)}")

if len(analysis_df) == 0:
    print("\n✗ No records with CRSP data. Cannot proceed.")
    exit()

# Connect to WRDS
print("\nConnecting to WRDS...")
db = wrds.Connection()
print("✓ Connected")

# STEP 1: Get PERMNOs using CIK codes via CRSP-Compustat link
print("\nStep 1: Matching CIKs to PERMNOs...")

# Get unique CIKs
ciks_with_crsp = analysis_df['CIK CODE'].dropna().unique().astype(int).tolist()
print(f"  Found {len(ciks_with_crsp)} unique CIKs")

# Create CIK list with proper string casting
cik_list = ','.join([f"'{str(c).zfill(10)}'" for c in ciks_with_crsp])  # Pad to 10 digits and quote

print("  Querying Compustat for GVKEY-CIK mapping...")
try:
    cik_gvkey_map = db.raw_sql(f"""
        SELECT DISTINCT cik, gvkey
        FROM comp.company
        WHERE cik IN ({cik_list})
    """)
    print(f"  ✓ Found GVKEYs for {len(cik_gvkey_map)} CIKs")
    
    # Convert CIK back to integer for merging
    cik_gvkey_map['cik'] = cik_gvkey_map['cik'].astype(int)
    
except Exception as e:
    print(f"  ✗ Error: {e}")
    print("\n  Your WRDS account may not have Compustat access.")
    print("  SOLUTION: Using market-adjusted returns instead...")
    
    # Create market-adjusted returns as fallback
    print("\n" + "=" * 60)
    print("FALLBACK: MARKET-ADJUSTED RETURNS")
    print("=" * 60)
    
    # Just use the original CARs (which are already market-adjusted)
    results_df = analysis_df[['breach_date', 'CIK CODE', 'car_5d', 'car_30d']].copy()
    results_df['breach_id'] = results_df.index
    results_df.columns = ['breach_date', 'CIK', 'car_5d_market_adj', 'car_30d_market_adj', 'breach_id']
    results_df['industry'] = 'Unknown'
    
    import os
    os.makedirs('Data/enrichment', exist_ok=True)
    results_df.to_csv('Data/enrichment/industry_adjusted_returns.csv', index=False)
    
    print(f"\n✓ Saved market-adjusted returns for {len(results_df)} breaches")
    print("  Note: These are market-adjusted, not industry-adjusted")
    print("  Your analysis can still proceed with these values")
    
    db.close()
    exit()

# Now link GVKEY to PERMNO
if len(cik_gvkey_map) > 0:
    gvkey_list = ','.join([f"'{g}'" for g in cik_gvkey_map['gvkey'].unique()])
    
    print("  Querying CRSP-Compustat link for PERMNOs...")
    gvkey_permno_map = db.raw_sql(f"""
        SELECT DISTINCT gvkey, lpermno as permno
        FROM crsp.ccmxpf_lnkhist
        WHERE gvkey IN ({gvkey_list})
        AND lpermno IS NOT NULL
        AND linktype IN ('LC', 'LU')
    """)
    
    print(f"  ✓ Found PERMNOs for {len(gvkey_permno_map)} GVKEYs")
    
    # Merge CIK -> GVKEY -> PERMNO
    cik_permno_map = cik_gvkey_map.merge(gvkey_permno_map, on='gvkey', how='inner')
    
    print(f"✓ Successfully linked {len(cik_permno_map)} CIKs to PERMNOs")
else:
    print("✗ No GVKEY mappings found")
    db.close()
    exit()

# Merge PERMNOs back to dataset
analysis_df = analysis_df.merge(cik_permno_map[['cik', 'permno']], 
                                 left_on='CIK CODE', right_on='cik', how='left')
analysis_df = analysis_df[analysis_df['permno'].notna()].copy()
analysis_df['permno'] = analysis_df['permno'].astype(int)

print(f"✓ {len(analysis_df)} breaches with valid PERMNO")

if len(analysis_df) == 0:
    print("\n✗ Could not match any CIKs to PERMNOs")
    db.close()
    exit()

# Get date range
min_date = analysis_df['breach_date'].min() - pd.DateOffset(days=60)
max_date = analysis_df['breach_date'].max() + pd.DateOffset(days=60)

print(f"\nDate range: {min_date.date()} to {max_date.date()}")

# STEP 2: Get industry classifications
print("\nStep 2: Getting industry classifications...")

permnos = analysis_df['permno'].dropna().unique().astype(int).tolist()
permno_list = ','.join([str(p) for p in permnos])

firm_industries = db.raw_sql(f"""
    SELECT permno, date, siccd
    FROM crsp.msf
    WHERE permno IN ({permno_list})
    AND date >= '{min_date.strftime('%Y-%m-%d')}'
    AND date <= '{max_date.strftime('%Y-%m-%d')}'
""")

print(f"✓ Got industry codes for {firm_industries['permno'].nunique()} firms")

# Map SIC to simplified industries
def sic_to_industry(sic):
    """Map SIC code to broad industry"""
    if pd.isna(sic):
        return 'Other'
    
    sic = int(sic)
    
    if 3570 <= sic <= 3579 or 3600 <= sic <= 3679 or 7370 <= sic <= 7379:
        return 'Technology'
    elif 4800 <= sic <= 4899:
        return 'Communications'
    elif 6000 <= sic <= 6999:
        return 'Financial'
    elif 2830 <= sic <= 2839 or 8000 <= sic <= 8099:
        return 'Healthcare'
    elif 5200 <= sic <= 5999:
        return 'Retail'
    elif 2000 <= sic <= 3999:
        return 'Manufacturing'
    else:
        return 'Other'

firm_industries['industry'] = firm_industries['siccd'].apply(sic_to_industry)

print("\nIndustry distribution:")
industry_dist = firm_industries.groupby('industry')['permno'].nunique()
print(industry_dist)

# STEP 3: Get firm returns
print("\nStep 3: Downloading firm returns...")

firm_returns = db.raw_sql(f"""
    SELECT permno, date, ret
    FROM crsp.dsf
    WHERE permno IN ({permno_list})
    AND date >= '{min_date.strftime('%Y-%m-%d')}'
    AND date <= '{max_date.strftime('%Y-%m-%d')}'
""")

print(f"✓ Downloaded {len(firm_returns)} firm-day return observations")

# Merge firm returns with industry classifications
firm_returns = firm_returns.merge(
    firm_industries[['permno', 'date', 'industry']], 
    on=['permno', 'date'], 
    how='left'
)

# Forward fill industry classification
firm_returns = firm_returns.sort_values(['permno', 'date'])
firm_returns['industry'] = firm_returns.groupby('permno')['industry'].ffill()

# STEP 4: Calculate industry returns
print("\nStep 4: Calculating industry returns...")

# Equal-weighted industry returns by date
industry_returns = firm_returns.groupby(['date', 'industry'])['ret'].mean().reset_index()
industry_returns.columns = ['date', 'industry', 'industry_return']

print(f"✓ Calculated {len(industry_returns)} industry-date return observations")

# STEP 5: Calculate industry-adjusted CARs
print("\nStep 5: Calculating industry-adjusted CARs for each breach...")

results = []
total = len(analysis_df)

for i, (idx, row) in enumerate(analysis_df.iterrows(), 1):
    if i % 50 == 0:
        print(f"  Progress: {i}/{total} ({i/total*100:.1f}%)")
    
    permno = int(row['permno'])
    breach_date = pd.to_datetime(row['breach_date'])
    
    # Get firm's industry
    firm_ind = firm_industries[
        (firm_industries['permno'] == permno) &
        (firm_industries['date'] <= breach_date)
    ].sort_values('date').tail(1)
    
    if len(firm_ind) == 0:
        industry = 'Other'
    else:
        industry = firm_ind['industry'].values[0]
    
    # Event windows
    event_start_5d = breach_date - pd.DateOffset(days=1)
    event_end_5d = breach_date + pd.DateOffset(days=5)
    event_start_30d = breach_date - pd.DateOffset(days=1)
    event_end_30d = breach_date + pd.DateOffset(days=30)
    
    # Get firm returns
    firm_ret = firm_returns[
        (firm_returns['permno'] == permno) &
        (firm_returns['date'] >= event_start_30d) &
        (firm_returns['date'] <= event_end_30d)
    ].copy()
    
    # Get industry returns
    ind_ret = industry_returns[
        (industry_returns['industry'] == industry) &
        (industry_returns['date'] >= event_start_30d) &
        (industry_returns['date'] <= event_end_30d)
    ].copy()
    
    # Merge
    merged = firm_ret.merge(ind_ret[['date', 'industry_return']], on='date', how='left')
    
    # Calculate abnormal returns (firm return - industry return)
    merged['abnormal_return'] = merged['ret'] - merged['industry_return']
    
    # 5-day CAR
    car_5d_data = merged[
        (merged['date'] >= event_start_5d) &
        (merged['date'] <= event_end_5d)
    ]
    
    if len(car_5d_data) >= 3:
        car_5d_ind_adj = (car_5d_data['abnormal_return'].fillna(0) * 100).sum()
    else:
        car_5d_ind_adj = np.nan
    
    # 30-day CAR
    if len(merged) >= 15:
        car_30d_ind_adj = (merged['abnormal_return'].fillna(0) * 100).sum()
    else:
        car_30d_ind_adj = np.nan
    
    results.append({
        'breach_id': idx,
        'permno': permno,
        'CIK': row['CIK CODE'],
        'breach_date': breach_date,
        'industry': industry,
        'car_5d_industry_adj': car_5d_ind_adj,
        'car_30d_industry_adj': car_30d_ind_adj,
        'original_car_5d': row.get('car_5d', np.nan),
        'original_car_30d': row.get('car_30d', np.nan)
    })

results_df = pd.DataFrame(results)

# Calculate difference
results_df['car_5d_difference'] = results_df['car_5d_industry_adj'] - results_df['original_car_5d']
results_df['car_30d_difference'] = results_df['car_30d_industry_adj'] - results_df['original_car_30d']

# Summary
print("\n" + "=" * 60)
print("INDUSTRY-ADJUSTED CAR SUMMARY")
print("=" * 60)

print(f"\nSuccessfully calculated for {len(results_df)} breaches")

valid_5d = results_df['car_5d_industry_adj'].notna()
valid_30d = results_df['car_30d_industry_adj'].notna()

print("\n5-Day CAR Comparison:")
print(f"  Valid observations: {valid_5d.sum()}")
if valid_5d.sum() > 0:
    print(f"  Original mean: {results_df.loc[valid_5d, 'original_car_5d'].mean():.4f}%")
    print(f"  Industry-adj mean: {results_df.loc[valid_5d, 'car_5d_industry_adj'].mean():.4f}%")
    print(f"  Average difference: {results_df.loc[valid_5d, 'car_5d_difference'].mean():.4f}%")

print("\n30-Day CAR Comparison:")
print(f"  Valid observations: {valid_30d.sum()}")
if valid_30d.sum() > 0:
    print(f"  Original mean: {results_df.loc[valid_30d, 'original_car_30d'].mean():.4f}%")
    print(f"  Industry-adj mean: {results_df.loc[valid_30d, 'car_30d_industry_adj'].mean():.4f}%")
    print(f"  Average difference: {results_df.loc[valid_30d, 'car_30d_difference'].mean():.4f}%")

print("\nIndustry breakdown:")
print(results_df.groupby('industry')['car_30d_industry_adj'].agg(['count', 'mean']))

# Save
import os
os.makedirs('Data/enrichment', exist_ok=True)

results_df.to_csv('Data/enrichment/industry_adjusted_returns.csv', index=False)
print(f"\n✓ Saved to Data/enrichment/industry_adjusted_returns.csv")

db.close()

print("\n" + "=" * 60)
print("✓ SCRIPT 2 COMPLETE")
print("=" * 60)
print(f"\nCreated variables:")
print("  • car_5d_industry_adj")
print("  • car_30d_industry_adj")
print("  • industry")
print("  • permno (for future use)")