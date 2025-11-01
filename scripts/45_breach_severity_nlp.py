import pandas as pd
import numpy as np
import re

print("=" * 60)
print("SCRIPT 5: BREACH SEVERITY CLASSIFICATION (NLP)")
print("=" * 60)

# Load breach data
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')
print(f"\n✓ Loaded {len(df)} breach records")

# Define keyword dictionaries for classification
print("\nDefining breach type keywords...")

breach_keywords = {
    'pii_breach': [
        'social security', 'ssn', 'credit card', 'personal information',
        'personally identifiable', 'pii', 'driver license', 'passport',
        'national id', 'identity', 'names and addresses', 'date of birth',
        'financial information', 'bank account', 'customer data', 'personal data'
    ],
    'health_breach': [
        'hipaa', 'medical record', 'health information', 'phi',
        'protected health', 'patient data', 'medical history',
        'diagnosis', 'prescription', 'healthcare', 'health data',
        'medical data', 'patient information'
    ],
    'financial_breach': [
        'payment card', 'credit card', 'debit card', 'bank account',
        'financial data', 'transaction', 'payment information',
        'account number', 'routing number', 'wire transfer', 'banking'
    ],
    'ip_breach': [
        'intellectual property', 'trade secret', 'source code',
        'proprietary', 'patent', 'confidential business', 'corporate data',
        'r&d', 'research data', 'business intelligence'
    ],
    'ransomware': [
        'ransomware', 'encryption', 'ransom', 'locked', 'decrypt',
        'encrypted files', 'ransom payment', 'crypto', 'extortion'
    ],
    'nation_state': [
        'nation-state', 'apt', 'advanced persistent', 'state-sponsored',
        'chinese hackers', 'russian hackers', 'north korea', 'iran',
        'government-backed', 'espionage', 'state actor'
    ],
    'insider_threat': [
        'insider', 'employee', 'contractor', 'unauthorized access',
        'internal', 'staff member', 'privileged access', 'former employee'
    ],
    'ddos_attack': [
        'ddos', 'denial of service', 'distributed denial',
        'service disruption', 'network flood', 'dos attack'
    ],
    'phishing': [
        'phishing', 'spear phishing', 'email compromise',
        'business email compromise', 'bec', 'social engineering'
    ],
    'malware': [
        'malware', 'virus', 'trojan', 'worm', 'backdoor',
        'keylogger', 'spyware', 'botnet'
    ]
}

# Sensitivity scoring weights
sensitivity_weights = {
    'pii_breach': 3,
    'health_breach': 4,  # HIPAA violations are most severe
    'financial_breach': 3,
    'ip_breach': 2,
    'ransomware': 3,
    'nation_state': 3,
    'insider_threat': 2,
    'ddos_attack': 1,
    'phishing': 2,
    'malware': 2
}

def classify_breach_text(text):
    """Classify breach based on text description"""
    if pd.isna(text):
        return {key: 0 for key in breach_keywords.keys()}
    
    text_lower = str(text).lower()
    
    classifications = {}
    
    for breach_type, keywords in breach_keywords.items():
        # Check if any keyword appears in text
        found = any(keyword in text_lower for keyword in keywords)
        classifications[breach_type] = 1 if found else 0
    
    return classifications

print("\nClassifying breaches...")

# Try to find text columns
text_columns = []
possible_text_cols = ['breach_details', 'Description', 'incident_details', 
                      'information_affected', 'Details']

for col in possible_text_cols:
    if col in df.columns:
        text_columns.append(col)
        print(f"  Found text column: {col}")

if len(text_columns) == 0:
    print("  ⚠ No text description column found")
    print("  Will use organization name and type fields only")

# Classify breaches
results = []

for idx, row in df.iterrows():
    # Get text for classification - combine all available text fields
    text_parts = []
    
    # Add any text columns found
    for col in text_columns:
        if col in df.columns and pd.notna(row.get(col)):
            text_parts.append(str(row[col]))
    
    # Add other potentially useful fields
    if pd.notna(row.get('org_name')):
        text_parts.append(str(row['org_name']))
    if pd.notna(row.get('organization_type')):
        text_parts.append(str(row['organization_type']))
    if pd.notna(row.get('TYPE')):
        text_parts.append(str(row['TYPE']))
    
    # Combine all text
    text = ' '.join(text_parts)
    
    # Classify
    classifications = classify_breach_text(text)
    
    # Calculate severity score
    severity_score = sum(
        classifications[breach_type] * sensitivity_weights[breach_type]
        for breach_type in breach_keywords.keys()
    )
    
    # Calculate based on records affected (if available)
    # FIX: Convert to numeric first
    records_affected = row.get('total_affected', 0)
    
    # Convert to numeric, handling strings
    try:
        records_affected = pd.to_numeric(records_affected, errors='coerce')
        if pd.isna(records_affected):
            records_affected = 0
        else:
            records_affected = float(records_affected)
    except:
        records_affected = 0
    
    if records_affected > 0:
        # Log scale severity based on records
        if records_affected < 1000:
            records_severity = 1
        elif records_affected < 10000:
            records_severity = 2
        elif records_affected < 100000:
            records_severity = 3
        elif records_affected < 1000000:
            records_severity = 4
        else:
            records_severity = 5
    else:
        records_severity = 0
    
    # Combined severity score
    combined_severity = severity_score + records_severity
    
    # High severity flag (top quartile)
    high_severity = 1 if combined_severity >= 7 else 0
    
    # Multiple breach types (indicates complexity)
    num_breach_types = sum(classifications.values())
    complex_breach = 1 if num_breach_types >= 2 else 0
    
    result = {
        'breach_id': idx,
        **classifications,
        'severity_score': severity_score,
        'records_severity': records_severity,
        'records_affected_numeric': records_affected,
        'combined_severity_score': combined_severity,
        'high_severity_breach': high_severity,
        'num_breach_types': num_breach_types,
        'complex_breach': complex_breach
    }
    
    results.append(result)

results_df = pd.DataFrame(results)

# Summary statistics
print("\n" + "=" * 60)
print("BREACH CLASSIFICATION SUMMARY")
print("=" * 60)

print("\nBreach Type Prevalence:")
for breach_type in breach_keywords.keys():
    count = results_df[breach_type].sum()
    pct = (count / len(results_df)) * 100
    print(f"  {breach_type:20} {count:4} ({pct:5.1f}%)")

print(f"\nHigh severity breaches: {results_df['high_severity_breach'].sum()} ({results_df['high_severity_breach'].mean()*100:.1f}%)")
print(f"Complex breaches (multiple types): {results_df['complex_breach'].sum()} ({results_df['complex_breach'].mean()*100:.1f}%)")

print(f"\nSeverity score distribution:")
print(results_df['combined_severity_score'].describe())

print(f"\nBreach type combinations:")
type_combos = results_df['num_breach_types'].value_counts().sort_index()
print(type_combos)

# Most severe breaches
print(f"\nTop 10 most severe breaches:")
top_severe = results_df.nlargest(10, 'combined_severity_score')
print(top_severe[['breach_id', 'combined_severity_score', 'num_breach_types', 'records_affected_numeric']].to_string(index=False))

# Check which text columns had useful info
if len(text_columns) > 0:
    print(f"\n✓ Classification used text from: {', '.join(text_columns)}")
else:
    print(f"\n⚠ Classification based only on organization names and types")
    print("  Note: Results may be less accurate without detailed breach descriptions")

# Save results
import os
os.makedirs('Data/enrichment', exist_ok=True)

results_df.to_csv('Data/enrichment/breach_severity_classification.csv', index=False)
print(f"\n✓ Saved to Data/enrichment/breach_severity_classification.csv")

print("\n" + "=" * 60)
print("✓ SCRIPT 5 COMPLETE")
print("=" * 60)
print(f"\nCreated variables:")
print("  • pii_breach")
print("  • health_breach")
print("  • financial_breach")
print("  • ip_breach")
print("  • ransomware")
print("  • nation_state")
print("  • insider_threat")
print("  • ddos_attack")
print("  • phishing")
print("  • malware")
print("  • severity_score")
print("  • records_severity")
print("  • combined_severity_score")
print("  • high_severity_breach")
print("  • num_breach_types")
print("  • complex_breach")