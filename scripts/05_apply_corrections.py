import pandas as pd

# Load the manual mapping file
mapping = pd.read_excel('Data/processed/manual_vendor_mapping.xlsx')

# Comprehensive corrections based on NVD vendor names
additional_corrections = {
    # Telecom companies - most don't have software CVEs
    'Altice USA, Inc.': 'N/A',  # Cable/telecom, no software products
    'Boost Mobile': 'N/A',  # MVNO, uses other vendors' infrastructure
    'Cable One, Inc.': 'N/A',
    'CenturyLink': 'centurylink',  # They do have some networking products
    'Centurylink Communications': 'centurylink',
    'Charter Communication': 'N/A',
    'Charter Communications, Inc.': 'N/A',
    'Cricket Wireless LLC': 'N/A',
    'Frontier Communications': 'N/A',
    'Frontier Communications Parent, Inc.': 'N/A',
    'Mediacom Communications Corporation': 'N/A',
    
    # Utilities/Infrastructure - no software CVEs
    'American Electric Power': 'N/A',
    'Duke Energy Corporation': 'N/A',
    'Crown Castle': 'N/A',
    'CSX Transportation, Inc.': 'N/A',
    'Republic Services, Inc.': 'N/A',
    'WM Waste Management, Inc.': 'N/A',
    
    # Media/Entertainment - most don't develop software
    'Audacy, Inc': 'N/A',
    'iHeart Media Inc': 'N/A',
    'iHeartMedia + Entertainment, Inc.': 'N/A',
    'NBC Sports Group': 'N/A',
    'NBCUniversal': 'N/A',
    'Paramount': 'paramount',  # They might have some
    'Paramount Global': 'paramount',
    'Sinclair Broadcast Group, Inc.': 'N/A',
    'Sirius XM Radio, Inc.': 'N/A',
    'Sirius XM Satellite Radio': 'N/A',
    
    # Fox entities - check if they have software
    'Fox & Company CPAs, Inc.': 'N/A',
    'Fox Entertainment Group Inc.': 'N/A',
    'Fox Group': 'N/A',
    'Fox News LLC': 'N/A',
    
    # Warner/Time Warner
    'Time Warner Inc.': 'N/A',
    'TimeWarner': 'N/A',
    'Warner Bros. Distributing Inc.': 'N/A',
    'Warner Music Group Corp': 'N/A',
    'Warner Music, Inc.': 'N/A',
    'Home Box Office, Inc.': 'N/A',
    
    # Disney entities
    'Disney Consumer Products and Interactive Media': 'disney',
    'Doubletree Suites by Hilton Walt Disney World': 'N/A',  # Hotel, not Disney software
    
    # Sony entities - use 'sony' for all
    'Sony Card Marketing & Services Company': 'sony',
    'Sony Corporation of America': 'sony',
    'Sony Electronics Inc.': 'sony',
    'Sony Interactive Entertainment': 'sony',
    'Sony Interactive Entertainment, LLC': 'sony',
    'Sony Network Entertainment America Inc.': 'sony',
    'Sony Online Entertainment': 'sony',
    'Sony Online Entertainment LLC': 'sony',
    'Sony Pictures': 'sony',
    'Sony Pictures Entertainment Health and Welfare Benefits Plan': 'sony',
    'Sony Pictures Entertainment, Inc.': 'sony',
    
    # AT&T variants - all use 'att'
    'AT&T Group Health Plan': 'att',
    'ATT-Breach Notification': 'att',
    'ATT-SecurityBreach': 'att',
    'ATT-SecurityBreach2': 'att',
    
    # Sprint variants
    'Sprint Business': 'sprint',
    'Sprint Nextel': 'sprint',
    
    # T-Mobile variants already matched
    'T-Mobile US, Inc.': 't-mobile',
    'T-Mobile, USA': 't-mobile',
    
    # Verizon variants
    'Verizon Communications, Inc.': 'verizon',
    'Verizon Corporate Services Group Inc.': 'verizon',
    'Verizon Media': 'verizon',
    
    # Network equipment/services
    'Citrix Systems, Inc.': 'citrix',
    'Nokia Networks and Solutions US, LLC': 'nokia',
    
    # Cloud/SaaS
    'CrowdStrike Holdings, Inc.': 'crowdstrike',
    'Snowflake Inc.': 'snowflake',  # Should already be in exact matches
    
    # Tech companies
    'Motorola Mobility, Inc.': 'motorola',
    'Oracle USA, Inc.': 'oracle',
    'PayPal Holdings, Inc.': 'paypal',
    'Uber Technologies, Inc.': 'uber',
    'Yahoo! Inc.': 'yahoo',
    'Yahoo! Voices': 'yahoo',
    
    # DISH variants
    'DISH Network Corporation': 'dish',
    'DISH Network L.L.C.': 'dish',
    'DISH Network, LLC': 'dish',
    
    # GoDaddy variants
    'GoDaddy.com': 'godaddy',
    'GoDaddy.com, LLC': 'godaddy',
    
    # Comcast variants
    'Comcast Cable Communications LLC': 'comcast',
    'Comcast Cable Communications, Inc.': 'comcast',
    
    # HP variants
    'HP Enterprise Services': 'hpe',
    'HP Enterprise Services, LLC': 'hpe',
    
    # Hardware/Storage
    'Seagate Technology LLC': 'seagate',
    'Seagate US LLC': 'seagate',
    
    # Financial Services
    'Cencora, Inc.': 'N/A',  # Healthcare distribution
    'Fidelity National Information Services, Inc.': 'fis',
    'Fidelity National Technology Imaging (FNTI)': 'fis',
    'Global Payments, Inc.': 'N/A',  # Payment processor, not software vendor
    
    # Data Centers
    'CyrusOne, Inc.': 'N/A',
    
    # Media/Broadcasting
    'Gray Television, Inc.': 'N/A',
    'Gray, Inc.': 'N/A',
}

# Apply corrections
for idx, row in mapping.iterrows():
    company = row['Company']
    if company in additional_corrections and pd.isna(row['Corrected_Vendor']) or row['Corrected_Vendor'] == '':
        mapping.at[idx, 'Corrected_Vendor'] = additional_corrections[company]
        mapping.at[idx, 'Notes'] = 'Applied automated correction'

# Save updated mapping
mapping.to_excel('Data/processed/manual_vendor_mapping_updated.xlsx', index=False)

# Statistics
has_vendor = mapping[~mapping['Corrected_Vendor'].isin(['', 'N/A'])]['Corrected_Vendor'].notna().sum()
no_vendor = mapping[mapping['Corrected_Vendor'] == 'N/A'].shape[0]
still_empty = mapping[(mapping['Corrected_Vendor'].isna()) | (mapping['Corrected_Vendor'] == '')].shape[0]

print("=" * 60)
print("VENDOR MAPPING UPDATES APPLIED")
print("=" * 60)
print(f"\n✓ Updated file: Data/processed/manual_vendor_mapping_updated.xlsx")
print(f"\nMapping status:")
print(f"  Companies with vendors: {has_vendor}")
print(f"  Companies marked N/A: {no_vendor}")
print(f"  Still need review: {still_empty}")
print(f"\nTotal partial/no matches: {len(mapping)}")