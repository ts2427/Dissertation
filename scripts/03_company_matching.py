import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

print("=" * 60)
print("COMPANY-TO-VENDOR MATCHING ANALYSIS")
print("=" * 60)

# Load breach data
print("\n[1/4] Loading breach companies...")
df = pd.read_excel(r'Data\DataBreaches.xlsx', engine='openpyxl')
breach_companies = df['org_name'].unique()
print(f"✓ Found {len(breach_companies)} unique companies")

# Create normalized versions
breach_normalized = {}
for company in breach_companies:
    # Normalize: lowercase, remove common suffixes
    normalized = company.lower()
    normalized = normalized.replace(' incorporated', '').replace(' inc.', '').replace(' inc', '')
    normalized = normalized.replace(' corporation', '').replace(' corp.', '').replace(' corp', '')
    normalized = normalized.replace(' company', '').replace(' co.', '').replace(' co', '')
    normalized = normalized.replace(',', '').strip()
    breach_normalized[normalized] = company

print(f"\nSample normalized names:")
for i, (norm, orig) in enumerate(list(breach_normalized.items())[:5]):
    print(f"  {orig} → {norm}")

# Extract ALL vendors from NVD data
print(f"\n[2/4] Extracting vendors from NVD files...")
print("This will take 2-3 minutes for all 19 files...")

json_dir = Path(r'Data\JSON Files')
json_files = sorted(list(json_dir.glob('*.json')))

all_vendors = set()
vendor_cve_count = defaultdict(int)

for idx, json_file in enumerate(json_files, 1):
    print(f"  Processing {json_file.name} ({idx}/{len(json_files)})...")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        nvd_data = json.load(f)
    
    for vuln in nvd_data['vulnerabilities']:
        try:
            configs = vuln['cve'].get('configurations', [])
            for config in configs:
                for node in config.get('nodes', []):
                    for cpe_match in node.get('cpeMatch', []):
                        cpe_uri = cpe_match.get('criteria', '')
                        if cpe_uri.startswith('cpe:'):
                            parts = cpe_uri.split(':')
                            if len(parts) > 3:
                                vendor = parts[3]
                                all_vendors.add(vendor)
                                vendor_cve_count[vendor] += 1
        except (KeyError, IndexError):
            continue

print(f"\n✓ Found {len(all_vendors)} unique vendors in NVD")
print(f"✓ Total CVE records processed: {sum(vendor_cve_count.values())}")

# Matching analysis
print(f"\n[3/4] Matching companies to vendors...")

exact_matches = []
partial_matches = []
no_matches = []

for norm_name, orig_name in breach_normalized.items():
    # Check exact match
    if norm_name in all_vendors:
        exact_matches.append((orig_name, norm_name, vendor_cve_count[norm_name]))
    else:
        # Check partial match (company name in vendor or vice versa)
        found_partial = False
        for vendor in all_vendors:
            if norm_name in vendor or vendor in norm_name:
                partial_matches.append((orig_name, vendor, vendor_cve_count[vendor]))
                found_partial = True
                break
        
        if not found_partial:
            no_matches.append(orig_name)

# Results
print(f"\n[4/4] MATCHING RESULTS")
print("=" * 60)
print(f"Total companies in breach data: {len(breach_companies)}")
print(f"Exact matches: {len(exact_matches)}")
print(f"Partial matches: {len(partial_matches)}")
print(f"No matches: {len(no_matches)}")
print(f"Match rate: {(len(exact_matches) + len(partial_matches)) / len(breach_companies) * 100:.1f}%")

if exact_matches:
    print(f"\n✓ EXACT MATCHES ({len(exact_matches)}):")
    for orig, vendor, count in sorted(exact_matches, key=lambda x: x[2], reverse=True)[:10]:
        print(f"  {orig} → {vendor} ({count} CVEs)")

if partial_matches:
    print(f"\n⚠ PARTIAL MATCHES ({len(partial_matches)}) - First 10:")
    for orig, vendor, count in partial_matches[:10]:
        print(f"  {orig} ≈ {vendor} ({count} CVEs)")

if no_matches:
    print(f"\n✗ NO MATCHES ({len(no_matches)}) - First 10:")
    for company in no_matches[:10]:
        print(f"  {company}")

print("\n" + "=" * 60)
print("✓ MATCHING ANALYSIS COMPLETE")
print("=" * 60)

# Save results for reference
results_df = pd.DataFrame({
    'Company': [x[0] for x in exact_matches] + [x[0] for x in partial_matches] + no_matches,
    'Vendor': [x[1] for x in exact_matches] + [x[1] for x in partial_matches] + ['NO MATCH'] * len(no_matches),
    'CVE_Count': [x[2] for x in exact_matches] + [x[2] for x in partial_matches] + [0] * len(no_matches),
    'Match_Type': ['EXACT'] * len(exact_matches) + ['PARTIAL'] * len(partial_matches) + ['NONE'] * len(no_matches)
})

results_df.to_excel('Data/processed/company_vendor_matching.xlsx', index=False)
print(f"\n💾 Results saved to: Data/processed/company_vendor_matching.xlsx")