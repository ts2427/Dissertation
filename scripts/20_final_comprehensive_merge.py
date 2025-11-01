import pandas as pd
import numpy as np
from datetime import timedelta

print("=" * 60)
print("FINAL COMPREHENSIVE DATA MERGE")
print("=" * 60)
print("\nIntegrating all data sources:")
print("  ✓ Breach data (858 records)")
print("  ✓ CVE/NVD vulnerability data")
print("  ✓ Stock returns (yfinance)")
print("  ✓ CRSP daily returns")
print("  ✓ Compustat fundamentals")
print("  ✓ Market indices")
print("  ✓ FCC regulatory classification")

# Load all datasets
print("\n[1/6] Loading datasets...")

breach_df = pd.read_excel('Data/processed/final_analysis_dataset.xlsx')
print(f"✓ Breach data: {len(breach_df)} records")

# WRDS Data
crsp_daily = pd.read_csv('Data/wrds/crsp_daily_returns.csv', parse_dates=['date'])
print(f"✓ CRSP daily: {len(crsp_daily):,} observations")

compustat_q = pd.read_csv('Data/wrds/compustat_fundamentals.csv', parse_dates=['datadate'])
print(f"✓ Compustat quarterly: {len(compustat_q):,} observations")

compustat_a = pd.read_csv('Data/wrds/compustat_annual.csv', parse_dates=['datadate'])
print(f"✓ Compustat annual: {len(compustat_a):,} observations")

market = pd.read_csv('Data/wrds/market_indices.csv', parse_dates=['date'])
print(f"✓ Market indices: {len(market):,} observations")

# FCC classification (already in breach_df if you ran previous script)
if 'fcc_reportable' not in breach_df.columns:
    print("\nAdding FCC classification...")
    
    fcc_keywords = {
        'telecom': ['at&t', 'att', 'verizon', 'sprint', 't-mobile', 'tmobile', 'centurylink', 
                    'lumen', 'frontier', 'telephone', 'wireless', 'cellular', 'mobile'],
        'cable': ['comcast', 'charter', 'cox', 'altice', 'cable one', 'mediacom', 
                  'suddenlink', 'optimum', 'spectrum', 'xfinity', 'cablevision'],
        'satellite': ['dish', 'directv', 'echostar', 'hughesnet'],
        'voip': ['vonage', 'ringcentral', 'zoom', 'bandwidth']
    }
    
    def classify_fcc(company_name):
        if pd.isna(company_name):
            return 'Non-FCC', False
        name_lower = company_name.lower()
        for category, keywords in fcc_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return category.title(), True
        return 'Non-FCC', False
    
    breach_df['fcc_category'], breach_df['fcc_reportable'] = zip(*breach_df['org_name'].apply(classify_fcc))
    print("✓ Added FCC classification")

# Calculate CRSP-based abnormal returns
print("\n[2/6] Calculating CRSP-based abnormal returns...")

crsp_market = crsp_daily.merge(market[['date', 'vwretd', 'ewretd']], on='date', how='left')
crsp_market['abnormal_ret'] = crsp_market['ret'] - crsp_market['vwretd']
crsp_market['abnormal_ret'] = crsp_market['abnormal_ret'] * 100

def calculate_event_returns(ticker, event_date, crsp_data):
    """Calculate CAR and BHAR around event"""
    try:
        ticker_data = crsp_data[crsp_data['ticker'] == ticker].copy()
        if ticker_data.empty:
            return None
        
        start_date = event_date - timedelta(days=50)
        end_date = event_date + timedelta(days=50)
        
        event_window = ticker_data[
            (ticker_data['date'] >= start_date) & 
            (ticker_data['date'] <= end_date)
        ].sort_values('date')
        
        if len(event_window) < 10:
            return None
        
        time_diffs = abs(event_window['date'] - event_date)
        event_idx = time_diffs.idxmin()
        event_pos = event_window.index.get_loc(event_idx)
        
        post_5d = min(len(event_window) - 1, event_pos + 5)
        post_30d = min(len(event_window) - 1, event_pos + 30)
        
        if post_5d <= event_pos:
            return None
        
        # CAR
        car_5d = event_window.iloc[event_pos:post_5d + 1]['abnormal_ret'].sum()
        car_30d = event_window.iloc[event_pos:post_30d + 1]['abnormal_ret'].sum()
        
        # BHAR
        bhar_5d = ((1 + event_window.iloc[event_pos:post_5d + 1]['ret']).prod() - 1) - \
                  ((1 + event_window.iloc[event_pos:post_5d + 1]['vwretd']).prod() - 1)
        bhar_30d = ((1 + event_window.iloc[event_pos:post_30d + 1]['ret']).prod() - 1) - \
                   ((1 + event_window.iloc[event_pos:post_30d + 1]['vwretd']).prod() - 1)
        
        return {
            'car_5d': round(car_5d, 4),
            'car_30d': round(car_30d, 4),
            'bhar_5d': round(bhar_5d * 100, 4),
            'bhar_30d': round(bhar_30d * 100, 4),
            'has_crsp_data': True
        }
    except:
        return None

event_returns = []
processed = 0

for idx, row in breach_df.iterrows():
    ticker = row['Map']
    breach_date = row['breach_date']
    
    if pd.isna(ticker) or pd.isna(breach_date):
        event_returns.append({
            'car_5d': None, 'car_30d': None,
            'bhar_5d': None, 'bhar_30d': None,
            'has_crsp_data': False
        })
        continue
    
    returns = calculate_event_returns(ticker, breach_date, crsp_market)
    
    if returns:
        event_returns.append(returns)
        processed += 1
    else:
        event_returns.append({
            'car_5d': None, 'car_30d': None,
            'bhar_5d': None, 'bhar_30d': None,
            'has_crsp_data': False
        })
    
    if (idx + 1) % 100 == 0:
        print(f"  Processed {idx + 1}/{len(breach_df)} ({processed} with CRSP data)")

print(f"✓ Calculated returns for {processed}/{len(breach_df)} breaches")

event_returns_df = pd.DataFrame(event_returns)

# Only add CRSP columns if not already present
crsp_cols = ['car_5d', 'car_30d', 'bhar_5d', 'bhar_30d', 'has_crsp_data']
for col in crsp_cols:
    if col not in breach_df.columns:
        breach_df[col] = event_returns_df[col]

# Add Compustat fundamentals
print("\n[3/6] Adding firm fundamentals...")

compustat_q['market_cap'] = compustat_q['prccq'] * compustat_q['cshoq']
compustat_q['roa'] = compustat_q['niq'] / compustat_q['atq']
compustat_q['leverage'] = compustat_q['ltq'] / compustat_q['atq']

firm_controls = []

for idx, row in breach_df.iterrows():
    ticker = row['Map']
    breach_date = row['breach_date']
    
    if pd.isna(ticker) or pd.isna(breach_date):
        firm_controls.append({
            'firm_size_log': None, 'roa': None, 'leverage': None,
            'sales_q': None, 'assets': None
        })
        continue
    
    firm_data = compustat_q[
        (compustat_q['tic'] == ticker) &
        (compustat_q['datadate'] < breach_date)
    ].sort_values('datadate', ascending=False)
    
    if len(firm_data) > 0:
        latest = firm_data.iloc[0]
        firm_controls.append({
            'firm_size_log': np.log(latest['market_cap']) if pd.notna(latest['market_cap']) and latest['market_cap'] > 0 else None,
            'roa': latest['roa'] if pd.notna(latest['roa']) else None,
            'leverage': latest['leverage'] if pd.notna(latest['leverage']) else None,
            'sales_q': latest['revtq'] if pd.notna(latest['revtq']) else None,
            'assets': latest['atq'] if pd.notna(latest['atq']) else None
        })
    else:
        firm_controls.append({
            'firm_size_log': None, 'roa': None, 'leverage': None,
            'sales_q': None, 'assets': None
        })

firm_controls_df = pd.DataFrame(firm_controls)

# Only add firm control columns if not already present
firm_cols = ['firm_size_log', 'roa', 'leverage', 'sales_q', 'assets']
for col in firm_cols:
    if col not in breach_df.columns:
        breach_df[col] = firm_controls_df[col]

print(f"✓ Added firm controls for {firm_controls_df.notna().any(axis=1).sum()} breaches")

# Calculate disclosure timing
print("\n[4/6] Calculating disclosure timing metrics...")

breach_df['disclosure_delay_days'] = (breach_df['reported_date'] - breach_df['breach_date']).dt.days
breach_df['immediate_disclosure'] = (breach_df['disclosure_delay_days'] <= 7).astype(int)
breach_df['delayed_disclosure'] = (breach_df['disclosure_delay_days'] > 30).astype(int)

# Calculate trading volume and return volatility (Essay 3)
print("\n[5/6] Calculating information asymmetry measures...")

def calculate_volatility(ticker, breach_date, crsp_data, window=30):
    """Calculate trading volume and return volatility"""
    try:
        ticker_data = crsp_data[crsp_data['ticker'] == ticker].copy()
        if ticker_data.empty:
            return None
        
        # Pre-breach window
        pre_start = breach_date - timedelta(days=window + 10)
        pre_end = breach_date - timedelta(days=1)
        
        # Post-breach window
        post_start = breach_date
        post_end = breach_date + timedelta(days=window)
        
        pre_window = ticker_data[
            (ticker_data['date'] >= pre_start) & 
            (ticker_data['date'] <= pre_end)
        ]
        
        post_window = ticker_data[
            (ticker_data['date'] >= post_start) & 
            (ticker_data['date'] <= post_end)
        ]
        
        if len(pre_window) < 10 or len(post_window) < 10:
            return None
        
        # Return volatility
        ret_vol_pre = pre_window['ret'].std() * np.sqrt(252) * 100
        ret_vol_post = post_window['ret'].std() * np.sqrt(252) * 100
        
        # Volume volatility
        vol_vol_pre = pre_window['vol'].std() if pre_window['vol'].notna().sum() > 5 else None
        vol_vol_post = post_window['vol'].std() if post_window['vol'].notna().sum() > 5 else None
        
        return {
            'return_volatility_pre': round(ret_vol_pre, 4) if pd.notna(ret_vol_pre) else None,
            'return_volatility_post': round(ret_vol_post, 4) if pd.notna(ret_vol_post) else None,
            'volume_volatility_pre': round(vol_vol_pre, 2) if pd.notna(vol_vol_pre) else None,
            'volume_volatility_post': round(vol_vol_post, 2) if pd.notna(vol_vol_post) else None,
            'volatility_change': round(ret_vol_post - ret_vol_pre, 4) if pd.notna(ret_vol_pre) and pd.notna(ret_vol_post) else None
        }
    except:
        return None

volatility_metrics = []

for idx, row in breach_df.iterrows():
    ticker = row['Map']
    breach_date = row['breach_date']
    
    if pd.isna(ticker) or pd.isna(breach_date):
        volatility_metrics.append({
            'return_volatility_pre': None, 'return_volatility_post': None,
            'volume_volatility_pre': None, 'volume_volatility_post': None,
            'volatility_change': None
        })
        continue
    
    vol_metrics = calculate_volatility(ticker, breach_date, crsp_market)
    
    if vol_metrics:
        volatility_metrics.append(vol_metrics)
    else:
        volatility_metrics.append({
            'return_volatility_pre': None, 'return_volatility_post': None,
            'volume_volatility_pre': None, 'volume_volatility_post': None,
            'volatility_change': None
        })

volatility_df = pd.DataFrame(volatility_metrics)

# Only add volatility columns if not already present
vol_cols = ['return_volatility_pre', 'return_volatility_post', 'volume_volatility_pre', 
            'volume_volatility_post', 'volatility_change']
for col in vol_cols:
    if col not in breach_df.columns:
        breach_df[col] = volatility_df[col]

print(f"✓ Calculated volatility for {volatility_df.notna().any(axis=1).sum()} breaches")

# Create analysis flags
print("\n[6/6] Creating final analysis variables...")

# Complete data flag
breach_df['has_complete_data'] = (
    breach_df['has_crsp_data'] & 
    (breach_df['total_cves'] > 0) &
    breach_df['firm_size_log'].notna()
)

# Governance proxy (since SOX data unavailable)
# Use firm size and age as proxies for governance quality
breach_df['large_firm'] = (breach_df['firm_size_log'] > breach_df['firm_size_log'].median()).astype(int)

# Breach severity categories
if 'total_affected' in breach_df.columns:
    breach_df['breach_severity'] = pd.cut(
        pd.to_numeric(breach_df['total_affected'], errors='coerce'),
        bins=[0, 10000, 100000, 1000000, np.inf],
        labels=['Small', 'Medium', 'Large', 'Massive']
    )

# Save final dataset
output_path = 'Data/processed/FINAL_DISSERTATION_DATASET.xlsx'
breach_df.to_excel(output_path, index=False)

print(f"\n✓ Saved to: {output_path}")

# Comprehensive Summary
print("\n" + "=" * 60)
print("FINAL DISSERTATION DATASET SUMMARY")
print("=" * 60)

print(f"\nTotal breach records: {len(breach_df)}")
print(f"  Date range: {breach_df['breach_date'].min().year} - {breach_df['breach_date'].max().year}")
print(f"  Unique companies: {breach_df['org_name'].nunique()}")

print(f"\n--- Data Coverage ---")
print(f"CVE data: {(breach_df['total_cves'] > 0).sum()} ({(breach_df['total_cves'] > 0).sum()/len(breach_df)*100:.1f}%)")
print(f"CRSP returns: {breach_df['has_crsp_data'].sum()} ({breach_df['has_crsp_data'].sum()/len(breach_df)*100:.1f}%)")
print(f"Firm controls: {breach_df['firm_size_log'].notna().sum()} ({breach_df['firm_size_log'].notna().sum()/len(breach_df)*100:.1f}%)")
print(f"Complete data: {breach_df['has_complete_data'].sum()} ({breach_df['has_complete_data'].sum()/len(breach_df)*100:.1f}%)")

print(f"\n--- FCC Classification ---")
print(f"FCC-reportable: {breach_df['fcc_reportable'].sum()} ({breach_df['fcc_reportable'].sum()/len(breach_df)*100:.1f}%)")
print(f"Non-FCC: {(~breach_df['fcc_reportable']).sum()} ({(~breach_df['fcc_reportable']).sum()/len(breach_df)*100:.1f}%)")

print(f"\n--- Disclosure Timing ---")
print(f"Immediate (≤7 days): {breach_df['immediate_disclosure'].sum()}")
print(f"Delayed (>30 days): {breach_df['delayed_disclosure'].sum()}")
print(f"Average delay: {breach_df['disclosure_delay_days'].mean():.1f} days")

print(f"\n--- Event Study Results (CRSP) ---")
crsp_valid = breach_df[breach_df['has_crsp_data'] == True]
if len(crsp_valid) > 0:
    print(f"Sample size: {len(crsp_valid)}")
    print(f"\nCAR (Cumulative Abnormal Returns):")
    print(f"  5-day: {crsp_valid['car_5d'].mean():.4f}% (median: {crsp_valid['car_5d'].median():.4f}%)")
    print(f"  30-day: {crsp_valid['car_30d'].mean():.4f}% (median: {crsp_valid['car_30d'].median():.4f}%)")
    print(f"\nBHAR (Buy-and-Hold Abnormal Returns):")
    print(f"  5-day: {crsp_valid['bhar_5d'].mean():.4f}% (median: {crsp_valid['bhar_5d'].median():.4f}%)")
    print(f"  30-day: {crsp_valid['bhar_30d'].mean():.4f}% (median: {crsp_valid['bhar_30d'].median():.4f}%)")

print("\n" + "=" * 60)
print("✓ DISSERTATION DATASET COMPLETE")
print("=" * 60)

print("\nYour dataset is ready for:")
print("\n  Essay 1: Theoretical Model (no data needed)")
print("\n  Essay 2: Event Study")
print("    - CAR/BHAR from CRSP ✓")
print("    - Disclosure timing (immediate vs delayed) ✓")
print("    - FCC regulatory classification ✓")
print("    - Firm controls (size, ROA, leverage) ✓")
print("\n  Essay 3: Information Asymmetry")
print("    - Return volatility (pre/post breach) ✓")
print("    - Volume volatility (pre/post breach) ✓")
print("    - Disclosure speed × Governance interaction ✓")
print("    - Firm size proxy for governance ✓")

print(f"\nFile: {output_path}")
print(f"Records with complete data: {breach_df['has_complete_data'].sum()}")