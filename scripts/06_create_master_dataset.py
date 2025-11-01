import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

print("=" * 60)
print("BUILDING MASTER DATASET")
print("=" * 60)

# Load breach data
print("\n[1/5] Loading breach data...")
breach_df = pd.read_excel(r'Data\DataBreaches.xlsx', engine='openpyxl')
print(f"✓ Loaded {len(breach_df)} breach records")

# Load vendor mappings
print("\n[2/5] Loading vendor mappings...")
exact_matches = pd.read_excel('Data/processed/company_vendor_matching.xlsx')
exact_matches = exact_matches[exact_matches['Match_Type'] == 'EXACT'][['Company', 'Vendor']]

corrected_matches = pd.read_excel('Data/processed/manual_vendor_mapping_updated.xlsx')
# Only keep companies with valid vendors (not N/A or empty)
corrected_matches = corrected_matches[
    (corrected_matches['Corrected_Vendor'].notna()) & 
    (corrected_matches['Corrected_Vendor'] != '') & 
    (corrected_matches['Corrected_Vendor'] != 'N/A')
][['Company', 'Corrected_Vendor']]
corrected_matches.rename(columns={'Corrected_Vendor': 'Vendor'}, inplace=True)

# Combine all mappings
all_mappings = pd.concat([exact_matches, corrected_matches], ignore_index=True)
print(f"✓ Total companies with vendor mappings: {len(all_mappings)}")

# Create company -> vendor lookup
company_to_vendor = dict(zip(all_mappings['Company'], all_mappings['Vendor']))

# Add vendor column to breach data
breach_df['nvd_vendor'] = breach_df['org_name'].map(company_to_vendor)

# Count how many breaches have vendor mappings
mapped_breaches = breach_df['nvd_vendor'].notna().sum()
print(f"✓ Breach records with vendor mappings: {mapped_breaches}/{len(breach_df)} ({mapped_breaches/len(breach_df)*100:.1f}%)")

# Extract CVE data for mapped vendors
print("\n[3/5] Extracting CVE data for mapped vendors...")
print("This will take 2-3 minutes...")

# Get unique vendors we need to extract
unique_vendors = breach_df['nvd_vendor'].dropna().unique()
print(f"Unique vendors to extract: {len(unique_vendors)}")

# Store CVE data by vendor
vendor_cves = defaultdict(list)
vendor_cve_counts = defaultdict(int)

json_dir = Path(r'Data\JSON Files')
json_files = sorted(list(json_dir.glob('*.json')))

for idx, json_file in enumerate(json_files, 1):
    print(f"  Processing {json_file.name} ({idx}/{len(json_files)})...")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        nvd_data = json.load(f)
    
    for vuln in nvd_data['vulnerabilities']:
        try:
            cve_id = vuln['cve']['id']
            published = vuln['cve'].get('published', '')
            
            # Extract vendors from this CVE
            cve_vendors = set()
            configs = vuln['cve'].get('configurations', [])
            for config in configs:
                for node in config.get('nodes', []):
                    for cpe_match in node.get('cpeMatch', []):
                        cpe_uri = cpe_match.get('criteria', '')
                        if cpe_uri.startswith('cpe:'):
                            parts = cpe_uri.split(':')
                            if len(parts) > 3:
                                vendor = parts[3]
                                cve_vendors.add(vendor)
            
            # Store CVE for matching vendors
            for vendor in cve_vendors:
                if vendor in unique_vendors:
                    vendor_cves[vendor].append({
                        'cve_id': cve_id,
                        'published': published,
                        'year': published[:4] if published else None
                    })
                    vendor_cve_counts[vendor] += 1
                    
        except (KeyError, IndexError):
            continue

print(f"\n✓ Extracted CVE data for {len(vendor_cves)} vendors")
print(f"✓ Total CVE records: {sum(vendor_cve_counts.values())}")

# Calculate CVE metrics for each breach
print("\n[4/5] Calculating CVE metrics for each breach...")

cve_metrics = []

for idx, row in breach_df.iterrows():
    vendor = row['nvd_vendor']
    breach_date = row['breach_date']
    
    if pd.isna(vendor):
        # No vendor mapping
        cve_metrics.append({
            'total_cves': 0,
            'cves_1yr_before': 0,
            'cves_2yr_before': 0,
            'cves_5yr_before': 0,
        })
        continue
    
    # Get all CVEs for this vendor
    vendor_cve_list = vendor_cves.get(vendor, [])
    
    if not vendor_cve_list:
        cve_metrics.append({
            'total_cves': 0,
            'cves_1yr_before': 0,
            'cves_2yr_before': 0,
            'cves_5yr_before': 0,
        })
        continue
    
    # Count CVEs in different time windows before breach
    total = len(vendor_cve_list)
    
    if pd.notna(breach_date):
        breach_year = breach_date.year
        
        cves_1yr = sum(1 for cve in vendor_cve_list 
                      if cve['year'] and int(cve['year']) >= breach_year - 1 and int(cve['year']) < breach_year)
        cves_2yr = sum(1 for cve in vendor_cve_list 
                      if cve['year'] and int(cve['year']) >= breach_year - 2 and int(cve['year']) < breach_year)
        cves_5yr = sum(1 for cve in vendor_cve_list 
                      if cve['year'] and int(cve['year']) >= breach_year - 5 and int(cve['year']) < breach_year)
    else:
        cves_1yr = cves_2yr = cves_5yr = 0
    
    cve_metrics.append({
        'total_cves': total,
        'cves_1yr_before': cves_1yr,
        'cves_2yr_before': cves_2yr,
        'cves_5yr_before': cves_5yr,
    })

# Add metrics to breach dataframe
cve_metrics_df = pd.DataFrame(cve_metrics)
breach_final = pd.concat([breach_df, cve_metrics_df], axis=1)

# Save master dataset
print("\n[5/5] Saving master dataset...")
output_path = 'Data/processed/master_breach_dataset.xlsx'
breach_final.to_excel(output_path, index=False)

print(f"✓ Saved to: {output_path}")

# Summary statistics
print("\n" + "=" * 60)
print("DATASET SUMMARY")
print("=" * 60)

print(f"\nTotal breach records: {len(breach_final)}")
print(f"Records with vendor mapping: {breach_final['nvd_vendor'].notna().sum()}")
print(f"Records with CVE data: {(breach_final['total_cves'] > 0).sum()}")

print(f"\nCVE Statistics:")
print(f"  Total unique vendors: {len(vendor_cves)}")
print(f"  Total CVE records: {sum(vendor_cve_counts.values())}")
print(f"  Avg CVEs per vendor: {sum(vendor_cve_counts.values()) / len(vendor_cves):.0f}")

print(f"\nTop vendors by CVE count:")
for vendor, count in sorted(vendor_cve_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {vendor}: {count:,} CVEs")

print(f"\nBreach records by year:")
year_counts = breach_final['breach_date'].dt.year.value_counts().sort_index()
for year, count in year_counts.items():
    print(f"  {int(year)}: {count} breaches")

print("\n" + "=" * 60)
print("✓ MASTER DATASET COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Review master_breach_dataset.xlsx")
print("2. Add stock price data using the 'Map' column (ticker symbols)")
print("3. Perform statistical analysis on CVE counts vs breach impact")