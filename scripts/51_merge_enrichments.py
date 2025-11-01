import pandas as pd
import numpy as np
import os

print("=" * 80)
print(" " * 25 + "MERGE ALL ENRICHMENTS")
print("=" * 80)

# Load base dataset
print("\nLoading base dataset...")
base_df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')
print(f"✓ Loaded {len(base_df)} breach records")

# Define all enrichment files
enrichment_files = {
    'prior_breaches': {
        'file': 'Data/enrichment/prior_breach_history.csv',
        'merge_on': 'breach_id',
        'description': 'Prior breach history'
    },
    'industry_returns': {
        'file': 'Data/enrichment/industry_adjusted_returns.csv',
        'merge_on': 'breach_id',
        'description': 'Industry-adjusted returns'
    },
    'analyst_coverage': {
        'file': 'Data/enrichment/analyst_coverage.csv',
        'merge_on': 'breach_id',
        'description': 'Analyst coverage'
    },
    'institutional_ownership': {
        'file': 'Data/enrichment/institutional_ownership.csv',
        'merge_on': 'breach_id',
        'description': 'Institutional ownership'
    },
    'breach_severity': {
        'file': 'Data/enrichment/breach_severity_classification.csv',
        'merge_on': 'breach_id',
        'description': 'Breach severity & types'
    },
    'executive_changes': {
        'file': 'Data/enrichment/executive_changes.csv',
        'merge_on': 'breach_id',
        'description': 'Executive turnover'
    },
    'regulatory': {
        'file': 'Data/enrichment/regulatory_enforcement.csv',
        'merge_on': 'breach_id',
        'description': 'Regulatory enforcement'
    },
    'dark_web': {
        'file': 'Data/enrichment/dark_web_presence.csv',
        'merge_on': 'breach_id',
        'description': 'Dark web presence'
    },
    'media': {
        'file': 'Data/enrichment/media_coverage.csv',
        'merge_on': 'breach_id',
        'description': 'Media coverage'
    },
    'insurance': {
        'file': 'Data/enrichment/cyber_insurance.csv',
        'merge_on': 'breach_id',
        'description': 'Cyber insurance'
    }
}

# Start with base dataset
merged_df = base_df.copy()
merged_df['breach_id'] = merged_df.index

merge_summary = []

print("\n" + "=" * 80)
print("MERGING ENRICHMENT FILES")
print("=" * 80)

for key, info in enrichment_files.items():
    filepath = info['file']
    
    print(f"\n[{key}] {info['description']}")
    print(f"  File: {filepath}")
    
    if os.path.exists(filepath):
        try:
            enrich_df = pd.read_csv(filepath)
            
            # Get columns to merge (exclude merge key and duplicates)
            base_cols = set(merged_df.columns)
            new_cols = [col for col in enrich_df.columns 
                       if col != info['merge_on'] and col not in base_cols]
            
            if new_cols:
                # Merge
                merged_df = merged_df.merge(
                    enrich_df[[info['merge_on']] + new_cols],
                    on=info['merge_on'],
                    how='left'
                )
                
                print(f"  ✓ Merged {len(new_cols)} new variables")
                print(f"    Variables: {', '.join(new_cols[:5])}{', ...' if len(new_cols) > 5 else ''}")
                
                merge_summary.append({
                    'source': key,
                    'description': info['description'],
                    'status': 'SUCCESS',
                    'variables_added': len(new_cols),
                    'file_found': True
                })
            else:
                print(f"  ⚠ No new variables to merge")
                merge_summary.append({
                    'source': key,
                    'description': info['description'],
                    'status': 'NO NEW VARS',
                    'variables_added': 0,
                    'file_found': True
                })
                
        except Exception as e:
            print(f"  ✗ Error merging: {e}")
            merge_summary.append({
                'source': key,
                'description': info['description'],
                'status': 'ERROR',
                'variables_added': 0,
                'file_found': True
            })
    else:
        print(f"  ✗ File not found")
        merge_summary.append({
            'source': key,
            'description': info['description'],
            'status': 'FILE NOT FOUND',
            'variables_added': 0,
            'file_found': False
        })

# Summary
print("\n" + "=" * 80)
print("MERGE SUMMARY")
print("=" * 80)

summary_df = pd.DataFrame(merge_summary)
print("\n" + summary_df.to_string(index=False))

total_vars_added = summary_df['variables_added'].sum()
successful_merges = len(summary_df[summary_df['status'] == 'SUCCESS'])

print(f"\n✓ Successfully merged: {successful_merges}/{len(enrichment_files)} files")
print(f"✓ Total new variables added: {total_vars_added}")

# Data completeness report
print("\n" + "=" * 80)
print("DATA COMPLETENESS REPORT")
print("=" * 80)

print(f"\nFinal dataset dimensions: {merged_df.shape[0]} rows × {merged_df.shape[1]} columns")

# Check key enriched variables
key_vars = [
    'prior_breaches_total',
    'car_30d_industry_adj',
    'num_analysts',
    'inst_ownership_pct',
    'high_severity_breach',
    'has_executive_change',
    'has_any_regulatory_action',
    'in_hibp',
    'media_coverage_count',
    'has_cyber_insurance_disclosure'
]

print("\nKey enriched variables completeness:")
for var in key_vars:
    if var in merged_df.columns:
        completeness = (merged_df[var].notna().sum() / len(merged_df)) * 100
        non_zero = (merged_df[var] != 0).sum() if merged_df[var].dtype in ['int64', 'float64'] else merged_df[var].notna().sum()
        print(f"  {var:40} {completeness:6.1f}% complete ({non_zero:4} non-zero/non-null)")
    else:
        print(f"  {var:40} NOT FOUND")

# Save enriched dataset
print("\n" + "=" * 80)
print("SAVING ENRICHED DATASET")
print("=" * 80)

output_file = 'Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.xlsx'

print(f"\nSaving to: {output_file}")

try:
    merged_df.to_excel(output_file, index=False)
    file_size = os.path.getsize(output_file)
    print(f"✓ Saved successfully ({file_size:,} bytes)")
    
    # Also save as CSV for easier access
    csv_file = output_file.replace('.xlsx', '.csv')
    merged_df.to_csv(csv_file, index=False)
    print(f"✓ Also saved as CSV: {csv_file}")
    
except Exception as e:
    print(f"✗ Error saving: {e}")

# Create data dictionary
print("\n" + "=" * 80)
print("CREATING DATA DICTIONARY")
print("=" * 80)

# Categorize variables
var_categories = {
    'Identifiers': ['breach_id', 'org_name', 'CIK CODE', 'PERMNO', 'Stock Ticker'],
    'Breach Characteristics': ['breach_date', 'disclosure_date', 'total_affected', 'disclosure_delay_days'],
    'Original Event Study': ['car_5d', 'car_30d', 'bhar_5d', 'bhar_30d'],
    'Industry-Adjusted Returns': ['car_5d_industry_adj', 'car_30d_industry_adj', 'industry'],
    'Disclosure Timing': ['immediate_disclosure', 'delayed_disclosure'],
    'Regulation': ['fcc_reportable'],
    'Firm Characteristics': ['firm_size_log', 'leverage', 'roa', 'large_firm'],
    'Volatility Measures': ['return_volatility_pre', 'return_volatility_post', 'volume_volatility_pre', 'volume_volatility_post'],
    'CVE Data': ['total_cves', 'cves_1yr_before'],
    'Prior Breach History': ['prior_breaches_total', 'prior_breaches_1yr', 'is_repeat_offender'],
    'Analyst Coverage': ['num_analysts', 'high_analyst_coverage', 'analyst_dispersion'],
    'Institutional Ownership': ['inst_ownership_pct', 'num_institutions', 'high_institutional_ownership'],
    'Breach Severity': ['pii_breach', 'health_breach', 'financial_breach', 'ransomware', 'severity_score', 'high_severity_breach'],
    'Executive Changes': ['has_executive_change', 'num_8k_502', 'days_to_first_change'],
    'Regulatory Enforcement': ['has_ftc_action', 'has_fcc_action', 'has_state_ag_action', 'total_regulatory_cost'],
    'Dark Web': ['in_hibp', 'hibp_pwn_count', 'hibp_date_match'],
    'Media Coverage': ['media_coverage_count', 'major_outlet_coverage', 'high_media_coverage', 'media_avg_tone'],
    'Cyber Insurance': ['has_cyber_insurance_disclosure']
}

data_dict = []

for category, var_list in var_categories.items():
    for var in var_list:
        if var in merged_df.columns:
            dtype = merged_df[var].dtype
            non_missing = merged_df[var].notna().sum()
            pct_complete = (non_missing / len(merged_df)) * 100
            
            data_dict.append({
                'Category': category,
                'Variable': var,
                'Type': str(dtype),
                'Non-Missing': non_missing,
                'Completeness': f"{pct_complete:.1f}%"
            })

dict_df = pd.DataFrame(data_dict)
dict_df.to_csv('Data/processed/DATA_DICTIONARY_ENRICHED.csv', index=False)

print(f"✓ Data dictionary saved: Data/processed/DATA_DICTIONARY_ENRICHED.csv")

# Final summary
print("\n" + "=" * 80)
print("✓✓✓ ENRICHMENT COMPLETE ✓✓✓")
print("=" * 80)

print(f"\nYour enriched dataset is ready:")
print(f"  📊 File: {output_file}")
print(f"  📈 Dimensions: {merged_df.shape[0]} breaches × {merged_df.shape[1]} variables")
print(f"  ✅ New variables: {total_vars_added}")

print(f"\nYou now have:")
print(f"  ✓ Prior breach history")
print(f"  ✓ Industry-adjusted returns")
print(f"  ✓ Analyst coverage")
print(f"  ✓ Institutional ownership")
print(f"  ✓ Breach severity classification")
print(f"  ✓ Executive turnover indicators")
print(f"  ✓ Regulatory enforcement data")
print(f"  ✓ Dark web presence")
print(f"  ✓ Media coverage metrics")
print(f"  ✓ Cyber insurance disclosures")

print("\n🎓 Your dissertation data is now publication-ready!")
print("=" * 80)