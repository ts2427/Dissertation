"""
Fix Unicode encoding issues in analysis scripts
"""
import re

# Files to fix
files_to_fix = [
    'notebooks/01_descriptive_statistics.py',
    'notebooks/02_essay2_event_study.py', 
    'notebooks/03_essay3_information_asymmetry.py',
    'notebooks/04_enrichment_analysis.py'
]

for filepath in files_to_fix:
    print(f"Fixing {filepath}...")
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace checkmark Unicode with [OK]
    content = content.replace('\\u2713', '[OK]')
    content = content.replace('✓', '[OK]')
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✓ Fixed!")

print("\n✅ All files fixed! Run python run_all.py again.")