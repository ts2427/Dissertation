import pandas as pd
import json
from pathlib import Path

def validate_breach_data(filepath):
    """Validate breach dataset structure and content"""
    print("Loading breach data...")
    df = pd.read_excel(filepath)
    print("✓ Breach data loaded successfully!")
    
    print("\n=== BREACH DATA VALIDATION ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nFirst few rows:\n{df.head()}")
    print(f"\nData types:\n{df.dtypes}")
    print(f"\nMissing values:\n{df.isnull().sum()}")
    
    return df

def validate_nvd_json(json_dir):
    """Test NVD JSON structure and extract vendor names"""
    print("\nSearching for JSON files...")
    json_files = sorted(list(Path(json_dir).glob('*.json')))
    print(f"✓ Found {len(json_files)} JSON files")
    
    print(f"\n=== NVD JSON VALIDATION ===")
    print(f"JSON files found: {len(json_files)}")
    
    if len(json_files) == 0:
        print("WARNING: No JSON files found!")
        return set()
    
    print(f"Year range: {json_files[0].name} to {json_files[-1].name}")
    
    # Test first file
    print(f"\nLoading first file: {json_files[0].name}...")
    with open(json_files[0], 'r', encoding='utf-8') as f:
        nvd_data = json.load(f)
    print("✓ JSON loaded successfully!")
    
    print(f"Vulnerabilities in first file: {len(nvd_data['vulnerabilities'])}")
    
    # Show structure of first CVE
    if len(nvd_data['vulnerabilities']) > 0:
        sample_cve = nvd_data['vulnerabilities'][0]['cve']
        print(f"\nSample CVE ID: {sample_cve['id']}")
        print(f"Published: {sample_cve.get('published', 'N/A')}")
        print(f"Keys in CVE: {list(sample_cve.keys())}")
    
    # Extract vendor names from sample
    print("\nExtracting vendor names from first 100 CVEs...")
    vendors = set()
    for i, vuln in enumerate(nvd_data['vulnerabilities'][:100]):
        if i % 25 == 0:
            print(f"  Processing CVE {i+1}/100...")
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
                                vendors.add(vendor)
        except (KeyError, IndexError):
            continue
    
    print(f"\n✓ Unique vendors found in sample: {len(vendors)}")
    print(f"Sample vendors: {sorted(list(vendors))[:20]}")
    return vendors

def test_name_matching(breach_df, nvd_vendors):
    """Test how many breach companies appear in NVD data"""
    
    print(f"\n=== NAME MATCHING TEST ===")
    print(f"Available columns in breach data: {breach_df.columns.tolist()}")
    
    # Try to identify the company column
    possible_company_cols = ['org_name', 'organization', 'company', 'name', 'entity', 'Organization']
    company_col = None
    
    for col in breach_df.columns:
        col_lower = col.lower()
        if any(possible in col_lower for possible in ['org', 'company', 'name', 'entity']):
            company_col = col
            break
    
    if company_col is None:
        print("\n⚠ Could not automatically identify company column.")
        print("Please specify which column contains company names.")
        return
    
    print(f"\nUsing column: '{company_col}'")
    print(f"Number of records: {len(breach_df)}")
    
    breach_companies = set(breach_df[company_col].dropna().astype(str).str.lower().str.strip().unique())
    nvd_vendors_lower = set(v.lower().replace('_', ' ') for v in nvd_vendors)
    
    # Exact matches
    exact_matches = breach_companies & nvd_vendors_lower
    
    print(f"\nUnique breach companies: {len(breach_companies)}")
    print(f"NVD vendors (from sample): {len(nvd_vendors_lower)}")
    print(f"Exact matches: {len(exact_matches)}")
    
    if len(breach_companies) > 0:
        print(f"Exact match rate: {len(exact_matches)/len(breach_companies)*100:.1f}%")
    
    if exact_matches:
        print(f"\n✓ Example exact matches: {sorted(list(exact_matches))[:10]}")
    
    print(f"\nSample breach companies: {sorted(list(breach_companies))[:15]}")
    print(f"\nSample NVD vendors: {sorted(list(nvd_vendors_lower))[:15]}")

if __name__ == "__main__":
    # CORRECTED - DataBreaches.xlsx is directly in Data folder
    breach_path = r'Data\DataBreaches.xlsx'  # Not in raw!
    nvd_path = r'Data\JSON Files'
    
    print("=" * 60)
    print("DATA VALIDATION SCRIPT")
    print("=" * 60)
    print(f"\nBreach data path: {breach_path}")
    print(f"NVD JSON path: {nvd_path}\n")