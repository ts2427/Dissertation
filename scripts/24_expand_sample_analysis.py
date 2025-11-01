import pandas as pd
import numpy as np

print("=" * 60)
print("SAMPLE SIZE ANALYSIS")
print("=" * 60)

# Load data
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')

print(f"\nTotal breach records: {len(df)}")

# Check each component
print("\n--- Data Availability ---")
print(f"Has CRSP data: {df['has_crsp_data'].sum()} ({df['has_crsp_data'].sum()/len(df)*100:.1f}%)")
print(f"Has CVE data (>0): {(df['total_cves'] > 0).sum()} ({(df['total_cves'] > 0).sum()/len(df)*100:.1f}%)")
print(f"Has firm controls: {df['firm_size_log'].notna().sum()} ({df['firm_size_log'].notna().sum()/len(df)*100:.1f}%)")
print(f"Has all three: {df['has_complete_data'].sum()} ({df['has_complete_data'].sum()/len(df)*100:.1f}%)")

# Alternative 1: Drop CVE requirement
alt1 = df[(df['has_crsp_data'] == True) & (df['firm_size_log'].notna())].copy()
print(f"\n--- Alternative 1: Without CVE Requirement ---")
print(f"Sample size: {len(alt1)} ({len(alt1)/len(df)*100:.1f}%)")

# Convert booleans
bool_cols = ['fcc_reportable', 'immediate_disclosure', 'delayed_disclosure']
for col in bool_cols:
    if col in alt1.columns:
        alt1[col] = alt1[col].astype(int)

# Quick regression test
import statsmodels.api as sm

reg_df = alt1[['car_30d', 'immediate_disclosure', 'fcc_reportable', 
               'firm_size_log', 'leverage']].dropna()

print(f"Regression sample: {len(reg_df)}")

X = sm.add_constant(reg_df[['immediate_disclosure', 'fcc_reportable', 
                             'firm_size_log', 'leverage']])
y = reg_df['car_30d']
model = sm.OLS(y, X).fit(cov_type='HC3')

print(f"\nKey Results (n={int(model.nobs)}):")
print(f"  Immediate disclosure: {model.params['immediate_disclosure']:.4f} (p={model.pvalues['immediate_disclosure']:.4f})")
print(f"  FCC regulation: {model.params['fcc_reportable']:.4f} (p={model.pvalues['fcc_reportable']:.4f})")
print(f"  R² = {model.rsquared:.4f}")

# Alternative 2: Use CVE as control only when available
print(f"\n--- Alternative 2: CVE as Optional Control ---")
print("Use full sample but include CVE dummy variable")

alt2 = alt1.copy()
alt2['has_cve_data'] = (alt2['total_cves'] > 0).astype(int)
alt2['cve_count_clean'] = alt2['total_cves'].fillna(0)

reg_df2 = alt2[['car_30d', 'immediate_disclosure', 'fcc_reportable', 
                'firm_size_log', 'leverage', 'has_cve_data']].dropna()

X2 = sm.add_constant(reg_df2[['immediate_disclosure', 'fcc_reportable', 
                              'firm_size_log', 'leverage', 'has_cve_data']])
model2 = sm.OLS(reg_df2['car_30d'], X2).fit(cov_type='HC3')

print(f"\nResults with CVE dummy (n={int(model2.nobs)}):")
print(f"  Immediate disclosure: {model2.params['immediate_disclosure']:.4f} (p={model2.pvalues['immediate_disclosure']:.4f})")
print(f"  FCC regulation: {model2.params['fcc_reportable']:.4f} (p={model2.pvalues['fcc_reportable']:.4f})")
print(f"  Has CVE data: {model2.params['has_cve_data']:.4f} (p={model2.pvalues['has_cve_data']:.4f})")
print(f"  R² = {model2.rsquared:.4f}")

# Alternative 3: Different sample for Essay 3
print(f"\n--- Alternative 3: Essay 3 Sample (Volatility Focus) ---")
print("Essay 3 doesn't need CVEs - it needs volatility measures")

alt3 = df[(df['return_volatility_pre'].notna()) & 
          (df['return_volatility_post'].notna()) &
          (df['firm_size_log'].notna())].copy()

print(f"Sample with volatility data: {len(alt3)} ({len(alt3)/len(df)*100:.1f}%)")

# Summary table
summary = pd.DataFrame({
    'Sample Definition': [
        'Original (All data)',
        'Essay 2 (Full Model with CVE)',
        'Alternative 1 (No CVE requirement)',
        'Alternative 2 (CVE as dummy)',
        'Alternative 3 (Essay 3 volatility)'
    ],
    'N': [
        len(df),
        215,
        len(alt1),
        len(reg_df2),
        len(alt3)
    ],
    'Percentage': [
        100.0,
        215/len(df)*100,
        len(alt1)/len(df)*100,
        len(reg_df2)/len(df)*100,
        len(alt3)/len(df)*100
    ]
})

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(summary.to_string(index=False))

print("\n" + "="*60)
print("RECOMMENDATION")
print("="*60)

print("\n📊 For Essay 2 (Disclosure Timing):")
print("   Option A: Keep n=215 with CVE controls (conservative, defensible)")
print("   Option B: Expand to ~700+ without CVE requirement")
print("   Option C: Use ~700+ with CVE dummy variable")

print("\n📊 For Essay 3 (Information Asymmetry):")
print(f"   Use volatility sample: n={len(alt3)} (CVE not needed for this essay)")

print("\n💡 My Recommendation:")
print("   • Essay 2 Main Analysis: Use expanded sample (~700 with CVE dummy)")
print("   • Essay 2 Robustness: Show n=215 with full CVE controls")
print("   • Essay 3: Use volatility-focused sample (~750)")
print("   • This maximizes power while maintaining rigor")