import pandas as pd
import os

print("=" * 60)
print("CHECKING SCRIPT 44 OUTPUT")
print("=" * 60)

# Check if the script exists
script_path = 'scripts/44_institutional_ownership.py'
if os.path.exists(script_path):
    print(f"✓ Script exists: {script_path}")
else:
    print(f"✗ Script not found: {script_path}")

# Check for any institutional ownership files
enrichment_dir = 'Data/enrichment'
possible_files = [
    'institutional_ownership.csv',
    'institutional_ownership_enhanced.csv',
    'inst_ownership.csv'
]

print(f"\nSearching for output files in {enrichment_dir}...")

for filename in possible_files:
    filepath = os.path.join(enrichment_dir, filename)
    if os.path.exists(filepath):
        print(f"\n✓ Found: {filename}")
        
        df = pd.read_csv(filepath)
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {df.columns.tolist()}")
        
        # Check data quality
        if 'inst_ownership_pct' in df.columns:
            has_data = df['inst_ownership_pct'].notna().sum()
            print(f"\n  Data Quality:")
            print(f"    Records with data: {has_data} ({has_data/len(df)*100:.1f}%)")
            
            if has_data > 0:
                print(f"    Mean ownership: {df['inst_ownership_pct'].mean():.2f}%")
                print(f"    Median ownership: {df['inst_ownership_pct'].median():.2f}%")
                print(f"    Range: {df['inst_ownership_pct'].min():.2f}% to {df['inst_ownership_pct'].max():.2f}%")
                
                print(f"\n  ✅ VERDICT: REAL DATA - Include in merge!")
                
                print(f"\n  Sample data:")
                print(df[df['inst_ownership_pct'].notna()].head(10))
            else:
                print(f"\n  ❌ VERDICT: PLACEHOLDER (all NaN) - Skip it")
        else:
            print(f"\n  ⚠ Column 'inst_ownership_pct' not found")
            print(f"  Available columns: {df.columns.tolist()}")
    else:
        print(f"✗ Not found: {filename}")

# List all files in enrichment directory
print(f"\n" + "=" * 60)
print("ALL FILES IN ENRICHMENT DIRECTORY:")
print("=" * 60)

if os.path.exists(enrichment_dir):
    files = os.listdir(enrichment_dir)
    for f in sorted(files):
        filepath = os.path.join(enrichment_dir, f)
        size = os.path.getsize(filepath) / 1024
        print(f"  {f:50} {size:8.1f} KB")
else:
    print("✗ Enrichment directory not found")