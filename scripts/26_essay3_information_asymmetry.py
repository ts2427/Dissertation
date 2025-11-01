import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("ESSAY 3: INFORMATION ASYMMETRY ANALYSIS")
print("=" * 60)

# Load data
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')

# Essay 3 Sample: Must have volatility measures
analysis_df = df[(df['return_volatility_pre'].notna()) & 
                 (df['return_volatility_post'].notna()) &
                 (df['firm_size_log'].notna())].copy()

# Convert booleans
bool_cols = ['fcc_reportable', 'immediate_disclosure', 'delayed_disclosure', 'large_firm']
for col in bool_cols:
    if col in analysis_df.columns:
        analysis_df[col] = analysis_df[col].astype(int)

print(f"✓ Analysis sample: {len(analysis_df)} records ({len(analysis_df)/len(df)*100:.1f}% of total)\n")

import os
os.makedirs('outputs/essay3/tables', exist_ok=True)
os.makedirs('outputs/essay3/figures', exist_ok=True)

# ============================================================
# CALCULATE INFORMATION ASYMMETRY MEASURES
# ============================================================

print("=" * 60)
print("INFORMATION ASYMMETRY MEASURES")
print("=" * 60)

# Change in volatility (key measure)
analysis_df['volatility_change'] = analysis_df['return_volatility_post'] - analysis_df['return_volatility_pre']
analysis_df['volatility_increase'] = (analysis_df['volatility_change'] > 0).astype(int)

# Relative change
analysis_df['volatility_pct_change'] = (analysis_df['volatility_change'] / 
                                        analysis_df['return_volatility_pre']) * 100

print("\nVolatility Statistics:")
print(f"  Pre-breach volatility (mean): {analysis_df['return_volatility_pre'].mean():.4f}%")
print(f"  Post-breach volatility (mean): {analysis_df['return_volatility_post'].mean():.4f}%")
print(f"  Mean change: {analysis_df['volatility_change'].mean():.4f}%")
print(f"  % with increased volatility: {analysis_df['volatility_increase'].mean()*100:.1f}%")

# Descriptive stats
desc_vars = ['return_volatility_pre', 'return_volatility_post', 'volatility_change',
             'volume_volatility_pre', 'volume_volatility_post']

desc_stats = analysis_df[desc_vars].describe().T
desc_stats['median'] = analysis_df[desc_vars].median()
desc_stats.to_csv('outputs/essay3/tables/table1_descriptive_stats.csv')

print("\n✓ Descriptive Statistics:")
print(desc_stats.round(4))

# ============================================================
# HYPOTHESIS 1: DISCLOSURE SPEED REDUCES ASYMMETRY
# ============================================================

print("\n" + "=" * 60)
print("H1: DISCLOSURE SPEED EFFECTS")
print("=" * 60)

immediate = analysis_df[analysis_df['immediate_disclosure'] == 1]
delayed = analysis_df[analysis_df['delayed_disclosure'] == 1]

print(f"\nImmediate Disclosure (n={len(immediate)}):")
print(f"  Mean volatility change: {immediate['volatility_change'].mean():.4f}%")
print(f"  % with increased volatility: {immediate['volatility_increase'].mean()*100:.1f}%")

print(f"\nDelayed Disclosure (n={len(delayed)}):")
print(f"  Mean volatility change: {delayed['volatility_change'].mean():.4f}%")
print(f"  % with increased volatility: {delayed['volatility_increase'].mean()*100:.1f}%")

ttest_vol = stats.ttest_ind(immediate['volatility_change'].dropna(), 
                             delayed['volatility_change'].dropna())
print(f"\nDifference: {immediate['volatility_change'].mean() - delayed['volatility_change'].mean():.4f}%")
print(f"T-test: t={ttest_vol[0]:.3f}, p={ttest_vol[1]:.4f}")

# ============================================================
# HYPOTHESIS 2: GOVERNANCE MODERATES EFFECTS
# ============================================================

print("\n" + "=" * 60)
print("H2: GOVERNANCE MODERATION")
print("=" * 60)

# Use firm size as governance proxy
large_firms = analysis_df[analysis_df['large_firm'] == 1]
small_firms = analysis_df[analysis_df['large_firm'] == 0]

print(f"\nLarge Firms (n={len(large_firms)}):")
print(f"  Mean volatility change: {large_firms['volatility_change'].mean():.4f}%")

print(f"\nSmall Firms (n={len(small_firms)}):")
print(f"  Mean volatility change: {small_firms['volatility_change'].mean():.4f}%")

ttest_gov = stats.ttest_ind(large_firms['volatility_change'].dropna(), 
                             small_firms['volatility_change'].dropna())
print(f"\nDifference: {large_firms['volatility_change'].mean() - small_firms['volatility_change'].mean():.4f}%")
print(f"T-test: t={ttest_gov[0]:.3f}, p={ttest_gov[1]:.4f}")

# ============================================================
# MULTIVARIATE REGRESSION
# ============================================================

print("\n" + "=" * 60)
print("MULTIVARIATE REGRESSION ANALYSIS")
print("=" * 60)

reg_df = analysis_df[['volatility_change', 'immediate_disclosure', 'large_firm',
                       'fcc_reportable', 'firm_size_log', 'leverage', 'roa']].dropna()

print(f"Regression sample: n={len(reg_df)}\n")

y = reg_df['volatility_change']

# Model 1: Disclosure speed only
X1 = sm.add_constant(reg_df[['immediate_disclosure']])
model1 = sm.OLS(y, X1).fit(cov_type='HC3')

# Model 2: Add governance (firm size)
X2 = sm.add_constant(reg_df[['immediate_disclosure', 'large_firm']])
model2 = sm.OLS(y, X2).fit(cov_type='HC3')

# Model 3: Add interaction
reg_df['disclosure_x_governance'] = reg_df['immediate_disclosure'] * reg_df['large_firm']
X3 = sm.add_constant(reg_df[['immediate_disclosure', 'large_firm', 'disclosure_x_governance']])
model3 = sm.OLS(y, X3).fit(cov_type='HC3')

# Model 4: Add FCC regulation
X4 = sm.add_constant(reg_df[['immediate_disclosure', 'large_firm', 'disclosure_x_governance', 
                              'fcc_reportable']])
model4 = sm.OLS(y, X4).fit(cov_type='HC3')

# Model 5: Full controls
X5 = sm.add_constant(reg_df[['immediate_disclosure', 'large_firm', 'disclosure_x_governance',
                              'fcc_reportable', 'firm_size_log', 'leverage']])
model5 = sm.OLS(y, X5).fit(cov_type='HC3')

models = [model1, model2, model3, model4, model5]

print("REGRESSION RESULTS:")
for i, model in enumerate(models, 1):
    print(f"\nModel {i}: N={int(model.nobs)}, R²={model.rsquared:.4f}")
    print(model.summary().tables[1])

# Save detailed output
with open('outputs/essay3/tables/regression_full_output.txt', 'w') as f:
    for i, model in enumerate(models, 1):
        f.write(f"\n{'='*60}\n")
        f.write(f"MODEL {i}\n")
        f.write(f"{'='*60}\n")
        f.write(str(model.summary()))
        f.write("\n\n")

# ============================================================
# FIGURES
# ============================================================

print("\n\nCreating figures...")

# Figure 1: Volatility change by disclosure timing
fig, ax = plt.subplots(figsize=(10, 7))
bp = ax.boxplot([immediate['volatility_change'].dropna(), 
                 delayed['volatility_change'].dropna()],
                labels=['Immediate\n(≤7 days)', 'Delayed\n(>30 days)'],
                patch_artist=True, widths=0.6)

for patch in bp['boxes']:
    patch.set_facecolor('lightcoral')
    patch.set_alpha(0.7)

ax.axhline(y=0, color='blue', linestyle='--', linewidth=2, alpha=0.7, label='No Change')
ax.set_ylabel('Change in Return Volatility (pp)', fontsize=13, fontweight='bold')
ax.set_title(f'Information Asymmetry by Disclosure Timing (n={len(analysis_df)})',
             fontsize=14, fontweight='bold')
ax.grid(axis='y', alpha=0.3)
ax.legend()

means = [immediate['volatility_change'].mean(), delayed['volatility_change'].mean()]
ax.scatter([1, 2], means, color='darkred', s=200, zorder=3, marker='D', 
           label=f'Means: {means[0]:.2f}, {means[1]:.2f}')

plt.tight_layout()
plt.savefig('outputs/essay3/figures/fig_volatility_by_timing.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: Interaction plot
imm_large = analysis_df[(analysis_df['immediate_disclosure'] == 1) & (analysis_df['large_firm'] == 1)]
imm_small = analysis_df[(analysis_df['immediate_disclosure'] == 1) & (analysis_df['large_firm'] == 0)]
del_large = analysis_df[(analysis_df['delayed_disclosure'] == 1) & (analysis_df['large_firm'] == 1)]
del_small = analysis_df[(analysis_df['delayed_disclosure'] == 1) & (analysis_df['large_firm'] == 0)]

means_large = [imm_large['volatility_change'].mean(), del_large['volatility_change'].mean()]
means_small = [imm_small['volatility_change'].mean(), del_small['volatility_change'].mean()]

fig, ax = plt.subplots(figsize=(10, 7))
ax.plot(['Immediate', 'Delayed'], means_large, marker='o', linewidth=2, 
        label='Large Firms', markersize=10)
ax.plot(['Immediate', 'Delayed'], means_small, marker='s', linewidth=2, 
        label='Small Firms', markersize=10)
ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax.set_ylabel('Mean Volatility Change (pp)', fontsize=13, fontweight='bold')
ax.set_title('Disclosure Timing × Firm Size Interaction', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/essay3/figures/fig_interaction.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ Figures created")

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "="*60)
print("✓✓✓ ESSAY 3 ANALYSIS COMPLETE ✓✓✓")
print("="*60)

print(f"\n📊 SAMPLE SIZE: n={len(reg_df)}")

print(f"\n🔑 KEY FINDINGS:")
print(f"  Immediate disclosure effect: {model5.params['immediate_disclosure']:.4f} (p={model5.pvalues['immediate_disclosure']:.4f})")
print(f"  Governance (large firm) effect: {model5.params['large_firm']:.4f} (p={model5.pvalues['large_firm']:.4f})")
print(f"  Interaction effect: {model5.params['disclosure_x_governance']:.4f} (p={model5.pvalues['disclosure_x_governance']:.4f})")

print("\n✅ Ready for Essay 3 write-up!")