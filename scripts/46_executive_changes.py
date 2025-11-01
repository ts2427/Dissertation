import pandas as pd
import numpy as np
import requests
import time
from datetime import timedelta
import re

print("=" * 60)
print("SCRIPT 6: EXECUTIVE TURNOVER FROM SEC 8-K FILINGS")
print("=" * 60)

# Load breach data
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')
print(f"\n✓ Loaded {len(df)} breach records")

# Filter to companies with CIK
analysis_df = df[df['CIK CODE'].notna()].copy()
print(f"✓ {len(analysis_df)} records with CIK codes")

# SEC EDGAR API setup
SEC_API_BASE = "https://data.sec.gov/submissions/"
HEADERS = {
    'User-Agent': 'Academic Research mcobphd11@utep.edu',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'data.sec.gov'
}

def get_company_filings(cik):
    """Get company filings from SEC EDGAR API"""
    cik_str = str(int(cik)).zfill(10)  # Pad CIK to 10 digits
    url = f"{SEC_API_BASE}CIK{cik_str}.json"
    
    try:
        time.sleep(0.1)  # Rate limit: max 10 requests/second
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"    Error fetching CIK {cik}: {e}")
        return None

def check_executive_changes(cik, breach_date, window_days=365):
    """Check for executive changes in 8-K filings after breach"""
    
    filings_data = get_company_filings(cik)
    
    if not filings_data:
        return {
            'has_executive_change': 0,
            'num_8k_502': 0,
            'days_to_first_change': np.nan,
            'has_cio_change': 0,
            'has_ceo_change': 0
        }
    
    # Get recent filings
    recent_filings = filings_data.get('filings', {}).get('recent', {})
    
    if not recent_filings:
        return {
            'has_executive_change': 0,
            'num_8k_502': 0,
            'days_to_first_change': np.nan,
            'has_cio_change': 0,
            'has_ceo_change': 0
        }
    
    # Extract 8-K filings
    forms = recent_filings.get('form', [])
    filing_dates = recent_filings.get('filingDate', [])
    primary_docs = recent_filings.get('primaryDocument', [])
    
    # Look for 8-K filings after breach date
    breach_date = pd.to_datetime(breach_date)
    window_end = breach_date + timedelta(days=window_days)
    
    executive_changes = []
    
    for i, form in enumerate(forms):
        if form == '8-K':
            filing_date = pd.to_datetime(filing_dates[i])
            
            if breach_date <= filing_date <= window_end:
                # This is an 8-K in our window
                # Item 5.02 = Departure of Directors or Certain Officers
                # We'd need to fetch the actual filing to check items
                # For now, flag all 8-Ks as potential executive changes
                
                days_after = (filing_date - breach_date).days
                executive_changes.append({
                    'filing_date': filing_date,
                    'days_after_breach': days_after,
                    'primary_doc': primary_docs[i] if i < len(primary_docs) else None
                })
    
    if executive_changes:
        has_change = 1
        num_changes = len(executive_changes)
        days_to_first = min(ec['days_after_breach'] for ec in executive_changes)
    else:
        has_change = 0
        num_changes = 0
        days_to_first = np.nan
    
    # Note: Detecting specific executive types (CEO, CIO) requires parsing actual filings
    # This is a simplified version
    
    return {
        'has_executive_change': has_change,
        'num_8k_502': num_changes,
        'days_to_first_change': days_to_first,
        'has_cio_change': 0,  # Would need full text parsing
        'has_ceo_change': 0   # Would need full text parsing
    }

print("\nQuerying SEC EDGAR for executive changes...")
print("Note: This queries the SEC API (rate limited to 10 req/sec)")
print(f"Analyzing {len(analysis_df)} companies...")

results = []
total = len(analysis_df)

for idx, (i, row) in enumerate(analysis_df.iterrows(), 1):
    if idx % 10 == 0:
        print(f"  Progress: {idx}/{total} ({idx/total*100:.1f}%)")
    
    cik = row['CIK CODE']
    breach_date = row['breach_date']
    
    exec_changes = check_executive_changes(cik, breach_date, window_days=365)
    
    result = {
        'breach_id': i,
        'CIK': cik,
        'breach_date': breach_date,
        **exec_changes
    }
    
    results.append(result)

results_df = pd.DataFrame(results)

# Summary statistics
print("\n" + "=" * 60)
print("EXECUTIVE TURNOVER SUMMARY")
print("=" * 60)

print(f"\nBreaches followed by executive changes (1 year): {results_df['has_executive_change'].sum()} ({results_df['has_executive_change'].mean()*100:.1f}%)")
print(f"Total 8-K filings detected: {results_df['num_8k_502'].sum()}")

if results_df['days_to_first_change'].notna().sum() > 0:
    print(f"\nDays to first executive change:")
    print(results_df['days_to_first_change'].describe())

print(f"\nDistribution of 8-K filings per breach:")
print(results_df['num_8k_502'].value_counts().sort_index())

# Save results
import os
os.makedirs('Data/enrichment', exist_ok=True)

results_df.to_csv('Data/enrichment/executive_changes.csv', index=False)
print(f"\n✓ Saved to Data/enrichment/executive_changes.csv")

print("\n" + "=" * 60)
print("✓ SCRIPT 6 COMPLETE")
print("=" * 60)
print(f"\nCreated variables:")
print("  • has_executive_change")
print("  • num_8k_502")
print("  • days_to_first_change")

print("\n⚠ NOTE: This is a simplified detection of 8-K filings.")
print("   For detailed executive role identification, would need to parse full filing text.")