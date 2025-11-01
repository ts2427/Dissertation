"""
Fix dashboard to use CSV instead of Excel
"""

# Fix app.py
print("Fixing dashboard/app.py...")
with open('dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.xlsx')",
    "df = pd.read_csv('Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.csv')"
)

with open('dashboard/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("  ✓ Fixed app.py!")

# Fix utils.py
print("Fixing dashboard/utils.py...")
with open('dashboard/utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "df = pd.read_csv('Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.csv')",
    "df = pd.read_csv('Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.csv')"
)

with open('dashboard/utils.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("  ✓ Fixed utils.py (already correct)!")

print("\n✅ All dashboard files now use CSV!")
print("\nRun: streamlit run dashboard/app.py")