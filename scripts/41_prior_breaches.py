import pandas as pd
import numpy as np
from datetime import timedelta

print("=" * 60)
print("SCRIPT 1: PRIOR BREACH HISTORY ANALYSIS")
print("=" * 60)

# Load data
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')
print(f"\n✓ Loaded {len(df)} breach records")

# Convert breach_date to datetime
df['breach_date'] = pd.to_datetime(df['breach_date'])

# Sort by organization and date
df = df.sort_values(['org_name', 'breach_date'])

print("\nCalculating breach history metrics...")

# For each breach, count prior breaches by same organization
breach_history = []

for idx, row in df.iterrows():
    org = row['org_name']
    breach_date = row['breach_date']
    
    # Count breaches by same org before this date
    prior_breaches = df[(df['org_name'] == org) & 
                        (df['breach_date'] < breach_date)].shape[0]
    
    # Days since last breach (if any)
    if prior_breaches > 0:
        last_breach = df[(df['org_name'] == org) & 
                        (df['breach_date'] < breach_date)]['breach_date'].max()
        days_since_last = (breach_date - last_breach).days
    else:
        days_since_last = np.nan
    
    # Count breaches in last 1, 3, 5 years
    prior_1yr = df[(df['org_name'] == org) & 
                   (df['breach_date'] < breach_date) &
                   (df['breach_date'] >= breach_date - timedelta(days=365))].shape[0]
    
    prior_3yr = df[(df['org_name'] == org) & 
                   (df['breach_date'] < breach_date) &
                   (df['breach_date'] >= breach_date - timedelta(days=1095))].shape[0]
    
    prior_5yr = df[(df['org_name'] == org) & 
                   (df['breach_date'] < breach_date) &
                   (df['breach_date'] >= breach_date - timedelta(days=1825))].shape[0]
    
    breach_history.append({
        'breach_id': idx,
        'org_name': org,
        'breach_date': breach_date,
        'prior_breaches_total': prior_breaches,
        'prior_breaches_1yr': prior_1yr,
        'prior_breaches_3yr': prior_3yr,
        'prior_breaches_5yr': prior_5yr,
        'days_since_last_breach': days_since_last,
        'is_repeat_offender': 1 if prior_breaches > 0 else 0,
        'is_first_breach': 1 if prior_breaches == 0 else 0
    })

history_df = pd.DataFrame(breach_history)

# Summary statistics
print("\n" + "=" * 60)
print("BREACH HISTORY SUMMARY")
print("=" * 60)

print(f"\nFirst-time breaches: {history_df['is_first_breach'].sum()} ({history_df['is_first_breach'].mean()*100:.1f}%)")
print(f"Repeat offenders: {history_df['is_repeat_offender'].sum()} ({history_df['is_repeat_offender'].mean()*100:.1f}%)")

print(f"\nOrganizations with multiple breaches:")
multi_breach = df.groupby('org_name').size()
multi_breach = multi_breach[multi_breach > 1].sort_values(ascending=False)
print(f"  Total: {len(multi_breach)} organizations")
print(f"  Max breaches by one org: {multi_breach.max()}")

print(f"\nTop 10 repeat offenders:")
print(multi_breach.head(10))

print(f"\nPrior breach distribution:")
print(history_df['prior_breaches_total'].describe())

# Save results
import os
os.makedirs('Data/enrichment', exist_ok=True)

history_df.to_csv('Data/enrichment/prior_breach_history.csv', index=False)
print(f"\n✓ Saved to Data/enrichment/prior_breach_history.csv")

# Also save summary by organization - FIXED VERSION
try:
    # Convert total_affected to numeric, coercing errors to NaN
    df['total_affected_numeric'] = pd.to_numeric(df['total_affected'], errors='coerce')
    
    org_summary = df.groupby('org_name').agg({
        'breach_date': ['count', 'min', 'max'],
        'total_affected_numeric': 'sum'  # Use numeric version
    }).round(0)
    
    org_summary.columns = ['total_breaches', 'first_breach_date', 'last_breach_date', 'total_records_affected']
    org_summary = org_summary.sort_values('total_breaches', ascending=False)
    
    org_summary.to_csv('Data/enrichment/organization_breach_summary.csv')
    print(f"✓ Saved organization summary to Data/enrichment/organization_breach_summary.csv")
    
except Exception as e:
    print(f"⚠ Warning: Could not create organization summary: {e}")
    print("  Main prior breach history file still saved successfully")

print("\n" + "=" * 60)
print("✓ SCRIPT 1 COMPLETE")
print("=" * 60)
print(f"\nCreated variables:")
print("  • prior_breaches_total")
print("  • prior_breaches_1yr")
print("  • prior_breaches_3yr") 
print("  • prior_breaches_5yr")
print("  • days_since_last_breach")
print("  • is_repeat_offender")
print("  • is_first_breach")