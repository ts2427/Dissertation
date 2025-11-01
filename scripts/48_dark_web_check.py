import pandas as pd
import numpy as np
import requests
import time

print("=" * 60)
print("SCRIPT 8: DARK WEB PRESENCE CHECK")
print("=" * 60)

# Load breach data
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')
print(f"\n✓ Loaded {len(df)} breach records")

# Have I Been Pwned API
HIBP_API_BASE = "https://haveibeenpwned.com/api/v3"
HIBP_HEADERS = {
    'User-Agent': 'DissertationResearch',
}

print("\nUsing Have I Been Pwned (HIBP) API to check breach presence...")
print("Note: HIBP tracks publicly disclosed breaches that appear in credential dumps")

def check_hibp_breach(company_name):
    """
    Check if company breach appears in HIBP database
    Note: Free API doesn't require key for breach search
    """
    
    try:
        # Get all breaches from HIBP
        time.sleep(1.5)  # Rate limit: be respectful
        url = f"{HIBP_API_BASE}/breaches"
        
        response = requests.get(url, headers=HIBP_HEADERS)
        
        if response.status_code == 200:
            breaches = response.json()
            
            # Search for company name in breach names
            company_lower = str(company_name).lower()
            
            for breach in breaches:
                breach_name = breach.get('Name', '').lower()
                breach_title = breach.get('Title', '').lower()
                
                # Check if company name appears in breach
                if company_lower in breach_name or company_lower in breach_title:
                    return {
                        'in_hibp': 1,
                        'hibp_breach_name': breach.get('Name'),
                        'hibp_breach_date': breach.get('BreachDate'),
                        'hibp_pwn_count': breach.get('PwnCount', 0),
                        'hibp_description': breach.get('Description', '')[:200],  # First 200 chars
                        'hibp_data_classes': '|'.join(breach.get('DataClasses', []))
                    }
            
            return {
                'in_hibp': 0,
                'hibp_breach_name': None,
                'hibp_breach_date': None,
                'hibp_pwn_count': 0,
                'hibp_description': None,
                'hibp_data_classes': None
            }
        
        else:
            return {
                'in_hibp': 0,
                'hibp_breach_name': None,
                'hibp_breach_date': None,
                'hibp_pwn_count': 0,
                'hibp_description': None,
                'hibp_data_classes': None
            }
    
    except Exception as e:
        print(f"    Error checking {company_name}: {e}")
        return {
            'in_hibp': 0,
            'hibp_breach_name': None,
            'hibp_breach_date': None,
            'hibp_pwn_count': 0,
            'hibp_description': None,
            'hibp_data_classes': None
        }

# Get unique companies (to avoid duplicate API calls)
unique_companies = df['org_name'].unique()
print(f"\nChecking {len(unique_companies)} unique companies...")

# Check each company once
company_hibp_data = {}

for i, company in enumerate(unique_companies, 1):
    if i % 10 == 0:
        print(f"  Progress: {i}/{len(unique_companies)} ({i/len(unique_companies)*100:.1f}%)")
    
    hibp_result = check_hibp_breach(company)
    company_hibp_data[company] = hibp_result

print("\n✓ HIBP checks complete")

# Map results back to all breaches
results = []

for idx, row in df.iterrows():
    company = row['org_name']
    breach_date = row['breach_date']
    
    hibp_data = company_hibp_data.get(company, {
        'in_hibp': 0,
        'hibp_breach_name': None,
        'hibp_breach_date': None,
        'hibp_pwn_count': 0,
        'hibp_description': None,
        'hibp_data_classes': None
    })
    
    # Check date proximity if HIBP breach exists
    if hibp_data['in_hibp'] == 1 and hibp_data['hibp_breach_date']:
        hibp_date = pd.to_datetime(hibp_data['hibp_breach_date'])
        prc_date = pd.to_datetime(breach_date)
        
        days_difference = abs((hibp_date - prc_date).days)
        date_match = 1 if days_difference <= 180 else 0  # Within 6 months
    else:
        days_difference = np.nan
        date_match = 0
    
    result = {
        'breach_id': idx,
        'org_name': company,
        'breach_date': breach_date,
        **hibp_data,
        'hibp_date_difference_days': days_difference,
        'hibp_date_match': date_match
    }
    
    results.append(result)

results_df = pd.DataFrame(results)

# Summary statistics
print("\n" + "=" * 60)
print("DARK WEB PRESENCE SUMMARY")
print("=" * 60)

print(f"\nBreaches found in HIBP: {results_df['in_hibp'].sum()} ({results_df['in_hibp'].mean()*100:.1f}%)")
print(f"Breaches with date match: {results_df['hibp_date_match'].sum()}")

if results_df['hibp_pwn_count'].sum() > 0:
    print(f"\nCredentials compromised (HIBP tracked):")
    print(f"  Total: {results_df['hibp_pwn_count'].sum():,.0f} accounts")
    print(f"  Mean per breach: {results_df[results_df['in_hibp']==1]['hibp_pwn_count'].mean():,.0f}")
    print(f"  Median per breach: {results_df[results_df['in_hibp']==1]['hibp_pwn_count'].median():,.0f}")

print(f"\nTop 10 breaches by credentials compromised:")
top_breaches = results_df.nlargest(10, 'hibp_pwn_count')[['org_name', 'hibp_breach_name', 'hibp_pwn_count']]
print(top_breaches.to_string(index=False))

if results_df['hibp_data_classes'].notna().sum() > 0:
    print(f"\nMost common data types compromised:")
    # Count data class occurrences
    all_classes = []
    for classes in results_df['hibp_data_classes'].dropna():
        all_classes.extend(classes.split('|'))
    
    from collections import Counter
    class_counts = Counter(all_classes)
    
    print("  Top 10:")
    for data_class, count in class_counts.most_common(10):
        print(f"    {data_class}: {count}")

# Save results
import os
os.makedirs('Data/enrichment', exist_ok=True)

results_df.to_csv('Data/enrichment/dark_web_presence.csv', index=False)
print(f"\n✓ Saved to Data/enrichment/dark_web_presence.csv")

print("\n" + "=" * 60)
print("✓ SCRIPT 8 COMPLETE")
print("=" * 60)
print(f"\nCreated variables:")
print("  • in_hibp")
print("  • hibp_breach_name")
print("  • hibp_breach_date")
print("  • hibp_pwn_count")
print("  • hibp_data_classes")
print("  • hibp_date_match")

print("\n⚠ NOTE: HIBP only tracks publicly disclosed breaches.")
print("   Not all breaches appear in credential dumps.")