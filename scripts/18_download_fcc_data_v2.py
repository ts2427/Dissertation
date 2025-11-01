import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

print("=" * 60)
print("FCC DATA BREACH NOTIFICATION DOWNLOAD")
print("=" * 60)

# Load your complete breach dataset
breach_df = pd.read_excel('Data/processed/final_analysis_dataset.xlsx')
print(f"\n✓ Loaded {len(breach_df)} breach records")
print(f"  Unique companies: {breach_df['org_name'].nunique()}")

# Classify companies by FCC jurisdiction
print("\n" + "=" * 60)
print("IDENTIFYING FCC-REPORTABLE COMPANIES")
print("=" * 60)

# FCC-reportable industry keywords
fcc_keywords = {
    'telecom': ['at&t', 'att', 'verizon', 'sprint', 't-mobile', 'tmobile', 'centurylink', 
                'lumen', 'frontier', 'telephone', 'wireless', 'cellular', 'mobile'],
    'cable': ['comcast', 'charter', 'cox', 'altice', 'cable one', 'mediacom', 
              'suddenlink', 'optimum', 'spectrum', 'xfinity', 'cablevision'],
    'satellite': ['dish', 'directv', 'echostar', 'hughesnet'],
    'voip': ['vonage', 'ringcentral', 'zoom', 'bandwidth']
}

def classify_fcc_jurisdiction(company_name):
    """Determine if company falls under FCC breach reporting"""
    if pd.isna(company_name):
        return 'Unknown', False
    
    name_lower = company_name.lower()
    
    for category, keywords in fcc_keywords.items():
        if any(keyword in name_lower for keyword in keywords):
            return category.title(), True
    
    return 'Non-FCC', False

breach_df['fcc_category'], breach_df['fcc_reportable'] = zip(*breach_df['org_name'].apply(classify_fcc_jurisdiction))

# Summary
fcc_reportable = breach_df[breach_df['fcc_reportable'] == True]
print(f"\n✓ FCC-Reportable Companies:")
print(f"  Total breaches: {len(fcc_reportable)} ({len(fcc_reportable)/len(breach_df)*100:.1f}%)")
print(f"  Unique companies: {fcc_reportable['org_name'].nunique()}")

print("\nBreakdown by category:")
for category in fcc_reportable['fcc_category'].value_counts().items():
    print(f"  {category[0]}: {category[1]} breaches")

print(f"\n✓ Non-FCC Companies: {len(breach_df) - len(fcc_reportable)} breaches")

# Show top FCC-reportable companies
print("\nTop FCC-reportable companies in your dataset:")
for company, count in fcc_reportable['org_name'].value_counts().head(15).items():
    category = fcc_reportable[fcc_reportable['org_name'] == company]['fcc_category'].iloc[0]
    print(f"  {company} ({category}): {count} breaches")

# Create FCC data directory
os.makedirs('Data/fcc', exist_ok=True)

print("\n" + "=" * 60)
print("FCC DATA DOWNLOAD INSTRUCTIONS")
print("=" * 60)

print("\nOFFICIAL FCC DATA SOURCE:")
print("  URL: https://www.fcc.gov/general/data-breach-notifications")
print("\nSTEPS:")
print("  1. Visit the FCC website above")
print("  2. Look for 'Breach Notifications' or 'View All Notifications'")
print("  3. Download the complete list (Excel or CSV)")
print("  4. Save to: Data/fcc/fcc_breach_notifications.csv")

# Check if file already exists
fcc_file = 'Data/fcc/fcc_breach_notifications.csv'

if os.path.exists(fcc_file):
    print("\n✓ FCC data file found!")
    
    try:
        fcc_data = pd.read_csv(fcc_file)
        print(f"  Loaded {len(fcc_data)} FCC breach notifications")
        print(f"\n  Columns in FCC data:")
        for col in fcc_data.columns:
            print(f"    - {col}")
        
        # Try to match with your data
        print("\n  Attempting to match FCC companies with your dataset...")
        
        # This will depend on the actual FCC data structure
        # We'll refine once we see the actual file
        
        # Save classification
        breach_df[['org_name', 'fcc_category', 'fcc_reportable']].drop_duplicates().to_csv(
            'Data/fcc/company_fcc_classification.csv', index=False
        )
        print("\n✓ Saved company classification to: Data/fcc/company_fcc_classification.csv")
        
    except Exception as e:
        print(f"\n✗ Error reading FCC file: {e}")
        
else:
    print("\n✗ FCC data file not found")
    
    # Try to access FCC website
    print("\nChecking FCC website availability...")
    
    try:
        url = "https://www.fcc.gov/general/data-breach-notifications"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print("✓ FCC website is accessible")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for table or data
            tables = soup.find_all('table')
            if tables:
                print(f"✓ Found {len(tables)} table(s) on page")
                print("  Data appears to be available on the website")
            
            # Look for download links
            links = soup.find_all('a', href=True)
            download_links = [l for l in links if any(x in str(l).lower() 
                            for x in ['download', 'export', 'csv', 'excel', 'xlsx'])]
            
            if download_links:
                print(f"\n✓ Found potential download links:")
                for link in download_links[:5]:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    print(f"  - {text}: {href}")
                    
        else:
            print(f"✗ Website returned status code: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Could not access website: {e}")

# Create expected FCC data template
print("\n" + "=" * 60)
print("EXPECTED FCC DATA FORMAT")
print("=" * 60)

fcc_template = pd.DataFrame({
    'Notification_Date': ['YYYY-MM-DD'],
    'Entity_Name': ['Company Name'],
    'FRN': ['FCC Registration Number'],
    'Breach_Date': ['YYYY-MM-DD'],
    'Date_Discovered': ['YYYY-MM-DD'],
    'Customers_Affected': [0],
    'Nature_of_Breach': ['Description'],
    'Type_of_Entity': ['Cable/Telecom/VoIP/Satellite']
})

template_path = 'Data/fcc/fcc_data_template.csv'
fcc_template.to_csv(template_path, index=False)
print(f"\n✓ Created template: {template_path}")

print("\nExpected FCC data columns:")
for col in fcc_template.columns:
    print(f"  - {col}")

# Save company classification for reference
breach_df[['org_name', 'breach_date', 'fcc_category', 'fcc_reportable']].to_csv(
    'Data/fcc/companies_to_match.csv', index=False
)
print(f"\n✓ Saved your companies list: Data/fcc/companies_to_match.csv")

print("\n" + "=" * 60)
print("NEXT STEPS")
print("=" * 60)

print(f"\n1. Download FCC breach data from FCC website")
print(f"2. Save as: Data/fcc/fcc_breach_notifications.csv")
print(f"3. Run: python scripts/19_validate_fcc_data.py")
print(f"   (This will match FCC data with your {len(fcc_reportable)} FCC-reportable breaches)")
print(f"4. Run: python scripts/20_merge_all_data.py")
print(f"   (Final comprehensive merge of all datasets)")

print(f"\nFCC-reportable companies in your dataset: {fcc_reportable['org_name'].nunique()}")
print(f"Non-FCC companies: {len(breach_df[breach_df['fcc_reportable'] == False]['org_name'].unique())}")
print(f"\nBoth groups are important for your analysis!")