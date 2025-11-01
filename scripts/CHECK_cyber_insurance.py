import pandas as pd

print("Checking cyber_insurance.csv...")

df = pd.read_csv('Data/enrichment/cyber_insurance.csv')

print(f"\nRows: {len(df)}")
print(f"Columns: {df.columns.tolist()}")

if 'has_cyber_insurance_disclosure' in df.columns:
    count = df['has_cyber_insurance_disclosure'].sum()
    print(f"\nFirms with cyber insurance: {count} ({count/len(df)*100:.1f}%)")
    
    if count > 5:
        print("✅ KEEP - Has meaningful data")
    else:
        print("❌ SKIP - Too sparse")
else:
    print("⚠ Column not found")