import pandas as pd
import json
from pathlib import Path

print("=" * 60)
print("QUICK DATA VALIDATION")
print("=" * 60)

# Step 1: Load breach data
print("\n[1/3] Loading breach data...")
try:
    df = pd.read_excel(r'Data\DataBreaches.xlsx', engine='openpyxl')
    print(f"✓ Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"\nFirst 3 rows:")
    print(df.head(3))
    print(f"\nData types:\n{df.dtypes}")
except Exception as e:
    print(f"✗ Error loading Excel: {e}")
    exit()

# Step 2: Check JSON files
print("\n[2/3] Checking JSON files...")
json_dir = Path(r'Data\JSON Files')
json_files = sorted(list(json_dir.glob('*.json')))
print(f"✓ Found {len(json_files)} JSON files")
print(f"Range: {json_files[0].name} to {json_files[-1].name}")

# Step 3: Test ONE JSON file
print("\n[3/3] Testing first JSON file structure...")
print(f"Loading {json_files[0].name}... (this may take 10-20 seconds)")

try:
    with open(json_files[0], 'r', encoding='utf-8') as f:
        nvd_data = json.load(f)
    
    print(f"✓ Loaded successfully!")
    print(f"Total CVEs in this file: {len(nvd_data['vulnerabilities'])}")
    
    # Check first CVE
    if len(nvd_data['vulnerabilities']) > 0:
        first_cve = nvd_data['vulnerabilities'][0]['cve']
        print(f"\nSample CVE:")
        print(f"  ID: {first_cve['id']}")
        print(f"  Published: {first_cve.get('published', 'N/A')}")
        
        # Try to extract ONE vendor
        print(f"\nLooking for vendor info in first CVE...")
        configs = first_cve.get('configurations', [])
        if configs:
            for config in configs:
                for node in config.get('nodes', []):
                    for cpe in node.get('cpeMatch', []):
                        cpe_uri = cpe.get('criteria', '')
                        if cpe_uri.startswith('cpe:'):
                            parts = cpe_uri.split(':')
                            if len(parts) > 3:
                                print(f"  Found vendor: {parts[3]}")
                                print(f"  Full CPE: {cpe_uri}")
                                break
                    break
                break
        else:
            print("  No configuration data in first CVE")
    
except Exception as e:
    print(f"✗ Error loading JSON: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✓ QUICK VALIDATION COMPLETE")
print("=" * 60)