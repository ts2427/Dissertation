import pandas as pd

# Read Excel file
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.xlsx')

# Save as CSV
df.to_csv('Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.csv', index=False)

print("✅ Converted Excel to CSV!")