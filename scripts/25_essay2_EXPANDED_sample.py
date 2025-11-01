import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("ESSAY 2: EXPANDED SAMPLE ANALYSIS (n=736)")
print("=" * 60)

# Load data
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')

# EXPANDED SAMPLE: CRSP + Firm Controls (no CVE requirement)
analysis_df = df[(df['has_crsp_data'] == True) & 
                 (df['firm_size_log'].notna())].copy()

# Convert booleans
bool_cols = ['fcc_reportable', 'immediate_disclosure', 'delayed_disclosure', 'large_firm']
for col in bool_cols:
    if col in analysis_df.columns:
        analysis_df[col] = analysis_df[col].astype(int)

print(f"✓ Analysis sample: {len(analysis_df)} records ({len(analysis_df)/len(df)*100:.1f}% of total)")

import os
os.makedirs('outputs/essay2_expanded/tables', exist_ok=True)
os.makedirs('outputs/essay2_expanded/figures', exist_ok=True)

# ============================================================
# DESCRIPTIVE STATISTICS
# ============================================================

print("\n" + "=" * 60)
print("DESCRIPTIVE STATISTICS")
print("=" * 60)

desc_vars = ['car_5d', 'car_30d', 'bhar_5d', 'bhar_30d', 
             'disclosure_delay_days', 'firm_size_log', 'leverage', 'roa']

desc_stats = analysis_df[desc_vars].describe().T
desc_stats['median'] = analysis_df[desc_vars].median()
desc_stats = desc_stats[['count', 'mean', 'median', 'std', 'min', 'max']]
desc_stats.to_csv('outputs/essay2_expanded/tables/table1_descriptives.csv')

print(desc_stats.round(4))

# Sample composition
composition = pd.DataFrame({
    'Category': ['Total Sample', 'FCC-Regulated', 'Non-FCC', 
                 'Immediate Disclosure', 'Delayed Disclosure'],
    'N': [
        len(analysis_df),
        analysis_df['fcc_reportable'].sum(),
        len(analysis_df) - analysis_df['fcc_reportable'].sum(),
        analysis_df['immediate_disclosure'].sum(),
        analysis_df['delayed_disclosure'].sum()
    ],
    'Percentage': [
        100.0,
        analysis_df['fcc_reportable'].mean() * 100,
        (1 - analysis_df['fcc_reportable'].mean()) * 100,
        analysis_df['immediate_disclosure'].mean() * 100,
        analysis_df['delayed_disclosure'].mean() * 100
    ]
})

print("\n✓ Sample Composition")
print(composition)

# ============================================================
# UNIVARIATE TESTS
# ============================================================

print("\n" + "=" * 60)
print("UNIVARIATE ANALYSIS")
print("=" * 60)

immediate = analysis_df[analysis_df['immediate_disclosure'] == 1]
delayed = analysis_df[analysis_df['delayed_disclosure'] == 1]

print(f"\nDisclosure Timing Comparison:")
print(f"  Immediate (≤7 days): n={len(immediate)}")
print(f"    Mean CAR (30-day): {immediate['car_30d'].mean():.4f}%")
print(f"  Delayed (>30 days): n={len(delayed)}")
print(f"    Mean CAR (30-day): {delayed['car_30d'].mean():.4f}%")

ttest_timing = stats.ttest_ind(immediate['car_30d'].dropna(), delayed['car_30d'].dropna())
print(f"  Difference: {immediate['car_30d'].mean() - delayed['car_30d'].mean():.4f}%")
print(f"  T-test: t={ttest_timing[0]:.3f}, p={ttest_timing[1]:.4f}")

fcc_reg = analysis_df[analysis_df['fcc_reportable'] == 1]
non_fcc = analysis_df[analysis_df['fcc_reportable'] == 0]

print(f"\nFCC Status Comparison:")
print(f"  FCC-Regulated: n={len(fcc_reg)}")
print(f"    Mean CAR (30-day): {fcc_reg['car_30d'].mean():.4f}%")
print(f"  Non-FCC: n={len(non_fcc)}")
print(f"    Mean CAR (30-day): {non_fcc['car_30d'].mean():.4f}%")

ttest_fcc = stats.ttest_ind(fcc_reg['car_30d'].dropna(), non_fcc['car_30d'].dropna())
print(f"  Difference: {fcc_reg['car_30d'].mean() - non_fcc['car_30d'].mean():.4f}%")
print(f"  T-test: t={ttest_fcc[0]:.3f}, p={ttest_fcc[1]:.4f}")

# ============================================================
# MAIN REGRESSIONS
# ============================================================

print("\n" + "=" * 60)
print("MULTIVARIATE REGRESSION ANALYSIS")
print("=" * 60)

reg_df = analysis_df[['car_30d', 'immediate_disclosure', 'fcc_reportable', 
                       'firm_size_log', 'leverage', 'roa']].dropna()

print(f"Regression sample: n={len(reg_df)}\n")

y = reg_df['car_30d']

# Model 1: Disclosure timing only
X1 = sm.add_constant(reg_df[['immediate_disclosure']])
model1 = sm.OLS(y, X1).fit(cov_type='HC3')

# Model 2: Add FCC
X2 = sm.add_constant(reg_df[['immediate_disclosure', 'fcc_reportable']])
model2 = sm.OLS(y, X2).fit(cov_type='HC3')

# Model 3: Add interaction
reg_df['fcc_x_immediate'] = reg_df['fcc_reportable'] * reg_df['immediate_disclosure']
X3 = sm.add_constant(reg_df[['immediate_disclosure', 'fcc_reportable', 'fcc_x_immediate']])
model3 = sm.OLS(y, X3).fit(cov_type='HC3')

# Model 4: Add firm controls
X4 = sm.add_constant(reg_df[['immediate_disclosure', 'fcc_reportable', 'fcc_x_immediate',
                              'firm_size_log', 'leverage']])
model4 = sm.OLS(y, X4).fit(cov_type='HC3')

# Model 5: Add ROA
X5 = sm.add_constant(reg_df[['immediate_disclosure', 'fcc_reportable', 'fcc_x_immediate',
                              'firm_size_log', 'leverage', 'roa']])
model5 = sm.OLS(y, X5).fit(cov_type='HC3')

models = [model1, model2, model3, model4, model5]

# Create regression table
print("="*60)
print("REGRESSION RESULTS TABLE")
print("="*60)

for i, model in enumerate(models, 1):
    print(f"\nModel {i}: N={int(model.nobs)}, R²={model.rsquared:.4f}")
    print(model.summary().tables[1])

# Save detailed output
with open('outputs/essay2_expanded/tables/regression_full_output.txt', 'w') as f:
    for i, model in enumerate(models, 1):
        f.write(f"\n{'='*60}\n")
        f.write(f"MODEL {i}\n")
        f.write(f"{'='*60}\n")
        f.write(str(model.summary()))
        f.write("\n\n")

# ============================================================
# ROBUSTNESS: CVE SUBSAMPLE
# ============================================================

print("\n" + "=" * 60)
print("ROBUSTNESS: CVE SUBSAMPLE (n=215)")
print("=" * 60)

# Filter to records with CVE data
cve_subsample = analysis_df[(analysis_df['total_cves'] > 0)].copy()
cve_reg_df = cve_subsample[['car_30d', 'immediate_disclosure', 'fcc_reportable', 
                             'firm_size_log', 'leverage', 'total_cves']].dropna()

print(f"CVE subsample: n={len(cve_reg_df)}")

cve_reg_df['fcc_x_immediate'] = cve_reg_df['fcc_reportable'] * cve_reg_df['immediate_disclosure']
X_cve = sm.add_constant(cve_reg_df[['immediate_disclosure', 'fcc_reportable', 'fcc_x_immediate',
                                     'firm_size_log', 'leverage', 'total_cves']])
model_cve = sm.OLS(cve_reg_df['car_30d'], X_cve).fit(cov_type='HC3')

print(f"\nCVE Subsample Results:")
print(model_cve.summary().tables[1])

# ============================================================
# COMPARISON TABLE
# ============================================================

comparison = pd.DataFrame({
    'Variable': ['Immediate Disclosure', 'FCC Regulated', 'FCC × Immediate', 'Firm Size', 'Leverage', 'Total CVEs'],
    'Full Sample (n=736)': [
        f"{model5.params['immediate_disclosure']:.4f} ({model5.pvalues['immediate_disclosure']:.3f})",
        f"{model5.params['fcc_reportable']:.4f} ({model5.pvalues['fcc_reportable']:.3f})",
        f"{model5.params['fcc_x_immediate']:.4f} ({model5.pvalues['fcc_x_immediate']:.3f})",
        f"{model5.params['firm_size_log']:.4f} ({model5.pvalues['firm_size_log']:.3f})",
        f"{model5.params['leverage']:.4f} ({model5.pvalues['leverage']:.3f})",
        'Not included'
    ],
    'CVE Subsample (n=215)': [
        f"{model_cve.params['immediate_disclosure']:.4f} ({model_cve.pvalues['immediate_disclosure']:.3f})",
        f"{model_cve.params['fcc_reportable']:.4f} ({model_cve.pvalues['fcc_reportable']:.3f})",
        f"{model_cve.params['fcc_x_immediate']:.4f} ({model_cve.pvalues['fcc_x_immediate']:.3f})",
        f"{model_cve.params['firm_size_log']:.4f} ({model_cve.pvalues['firm_size_log']:.3f})",
        f"{model_cve.params['leverage']:.4f} ({model_cve.pvalues['leverage']:.3f})",
        f"{model_cve.params['total_cves']:.6f} ({model_cve.pvalues['total_cves']:.3f})"
    ]
})

comparison.to_csv('outputs/essay2_expanded/tables/table_sample_comparison.csv', index=False)

print("\n" + "="*60)
print("SAMPLE COMPARISON")
print("="*60)
print(comparison.to_string(index=False))

# ============================================================
# FIGURES
# ============================================================

print("\n\nCreating figures...")

# Figure 1: CAR by timing
fig, ax = plt.subplots(figsize=(10, 7))
bp = ax.boxplot([immediate['car_30d'].dropna(), delayed['car_30d'].dropna()],
                labels=['Immediate\n(≤7 days)', 'Delayed\n(>30 days)'],
                patch_artist=True, widths=0.6)

for patch in bp['boxes']:
    patch.set_facecolor('lightblue')
    patch.set_alpha(0.7)

ax.axhline(y=0, color='red', linestyle='--', linewidth=2, alpha=0.7)
ax.set_ylabel('30-Day CAR (%)', fontsize=13, fontweight='bold')
ax.set_title(f'Market Reaction by Disclosure Timing (n={len(analysis_df)})', 
             fontsize=14, fontweight='bold')
ax.grid(axis='y', alpha=0.3)

means = [immediate['car_30d'].mean(), delayed['car_30d'].mean()]
ax.scatter([1, 2], means, color='darkred', s=200, zorder=3, marker='D')

plt.tight_layout()
plt.savefig('outputs/essay2_expanded/figures/fig_car_by_timing.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: CAR by FCC
fig, ax = plt.subplots(figsize=(10, 7))
bp = ax.boxplot([fcc_reg['car_30d'].dropna(), non_fcc['car_30d'].dropna()],
                labels=['FCC-Regulated', 'Non-Regulated'],
                patch_artist=True, widths=0.6)

colors = ['#ff7f0e', '#1f77b4']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax.axhline(y=0, color='red', linestyle='--', linewidth=2, alpha=0.7)
ax.set_ylabel('30-Day CAR (%)', fontsize=13, fontweight='bold')
ax.set_title(f'Market Reaction by Regulatory Status (n={len(analysis_df)})\n(p={ttest_fcc[1]:.4f})', 
             fontsize=14, fontweight='bold')
ax.grid(axis='y', alpha=0.3)

means = [fcc_reg['car_30d'].mean(), non_fcc['car_30d'].mean()]
ax.scatter([1, 2], means, color='darkred', s=200, zorder=3, marker='D')

plt.tight_layout()
plt.savefig('outputs/essay2_expanded/figures/fig_car_by_fcc.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ Figures created")

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "="*60)
print("✓✓✓ EXPANDED SAMPLE ANALYSIS COMPLETE ✓✓✓")
print("="*60)

print(f"\n📊 SAMPLE SIZES:")
print(f"  Main analysis: n={len(reg_df)}")
print(f"  CVE robustness: n={len(cve_reg_df)}")

print(f"\n🔑 KEY FINDINGS (Main Sample n={len(reg_df)}):")
print(f"  Immediate disclosure: {model5.params['immediate_disclosure']:.4f} (p={model5.pvalues['immediate_disclosure']:.4f})")
print(f"  FCC regulation: {model5.params['fcc_reportable']:.4f} (p={model5.pvalues['fcc_reportable']:.4f})")
print(f"  Interaction: {model5.params['fcc_x_immediate']:.4f} (p={model5.pvalues['fcc_x_immediate']:.4f})")

print(f"\n🔑 CVE SUBSAMPLE (n={len(cve_reg_df)}):")
print(f"  FCC regulation: {model_cve.params['fcc_reportable']:.4f} (p={model_cve.pvalues['fcc_reportable']:.4f})")
print(f"  CVE effect: {model_cve.params['total_cves']:.6f} (p={model_cve.pvalues['total_cves']:.4f})")

print("\n✅ Ready for dissertation write-up!")
print("   Use n=736 as main analysis")
print("   Use n=215 as robustness check")