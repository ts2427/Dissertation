import pandas as pd

# Load the automated results
results = pd.read_excel('Data/processed/company_vendor_matching.xlsx')

# Filter out the problematic partial matches and create a template for manual review
review_needed = results[results['Match_Type'].isin(['PARTIAL', 'NONE'])].copy()

# Add a column for manual correction
review_needed['Corrected_Vendor'] = ''
review_needed['Notes'] = ''

# Pre-fill some obvious corrections
corrections = {
    'Adobe Systems Incorporated': 'adobe',
    'Activision Publishing, Inc.': 'activision',
    'Cisco Systems, Inc.': 'cisco',
    'AT&T, Inc.': 'att',
    'AT&T Services, Inc.': 'att',
    'Hewlett Packard Company': 'hp',
    'Hewlett-Packard Company': 'hp',
    'Hewlett Packard Enterprise Company': 'hpe',
    'salesforce.com': 'salesforce',
    'Rocket Mortgage, LLC': 'quicken',
    'The Walt Disney Company': 'disney',
    'Spotify USA Inc.': 'spotify',
}

for idx, row in review_needed.iterrows():
    company = row['Company']
    if company in corrections:
        review_needed.at[idx, 'Corrected_Vendor'] = corrections[company]
        review_needed.at[idx, 'Notes'] = 'Auto-corrected based on known vendor'

# Save for manual review
review_needed.to_excel('Data/processed/manual_vendor_mapping.xlsx', index=False)

print("=" * 60)
print("MANUAL MAPPING FILE CREATED")
print("=" * 60)
print(f"\n✓ File saved: Data/processed/manual_vendor_mapping.xlsx")
print(f"\nCompanies needing review: {len(review_needed)}")
print(f"Pre-filled corrections: {sum(review_needed['Corrected_Vendor'] != '')}")
print(f"\nNext steps:")
print("1. Open the Excel file")
print("2. Fill in 'Corrected_Vendor' column with correct NVD vendor names")
print("3. Add notes for uncertain matches")
print("4. Save the file")
print("\nTip: Search NVD database at https://nvd.nist.gov to verify vendor names")