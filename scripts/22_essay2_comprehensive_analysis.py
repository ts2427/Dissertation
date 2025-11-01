import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.formula.api import ols
from scipy.stats import normaltest, shapiro

print("=" * 60)
print("ESSAY 2: COMPREHENSIVE EVENT STUDY ANALYSIS")
print("=" * 60)

# Load data
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')
print(f"\n✓ Loaded {len(df)} breach records")

# Filter to complete data
analysis_df = df[df['has_complete_data'] == True].copy()
print(f"✓ Analysis sample: {len(analysis_df)} records")

# Create output directories
import os
os.makedirs('outputs/essay2/tables', exist_ok=True)
os.makedirs('outputs/essay2/figures', exist_ok=True)
os.makedirs('outputs/essay2/robustness', exist_ok=True)

# ============================================================
# SECTION 1: DESCRIPTIVE STATISTICS
# ============================================================

print("\n" + "=" * 60)
print("SECTION 1: DESCRIPTIVE STATISTICS")
print("=" * 60)

# Table 1: Sample Characteristics
desc_vars = ['car_5d', 'car_30d', 'bhar_5d', 'bhar_30d', 
             'disclosure_delay_days', 'firm_size_log', 'leverage', 
             'roa', 'total_cves', 'cves_1yr_before']

desc_stats = analysis_df[desc_vars].describe().T
desc_stats['median'] = analysis_df[desc_vars].median()
desc_stats = desc_stats[['count', 'mean', 'median', 'std', 'min', 'max']]

desc_stats.to_csv('outputs/essay2/tables/table1_descriptive_stats.csv')
print("\n✓ Table 1: Descriptive Statistics")
print(desc_stats.round(4))

# Table 2: Sample Composition
composition = pd.DataFrame({
    'Category': ['Total Sample', 'FCC-Regulated', 'Non-FCC', 
                 'Immediate Disclosure', 'Delayed Disclosure',
                 'Large Firms', 'Small Firms'],
    'N': [
        len(analysis_df),
        analysis_df['fcc_reportable'].sum(),
        (~analysis_df['fcc_reportable']).sum(),
        analysis_df['immediate_disclosure'].sum(),
        analysis_df['delayed_disclosure'].sum(),
        analysis_df['large_firm'].sum(),
        (~analysis_df['large_firm']).sum()
    ],
    'Percentage': [
        100.0,
        analysis_df['fcc_reportable'].mean() * 100,
        (1 - analysis_df['fcc_reportable'].mean()) * 100,
        analysis_df['immediate_disclosure'].mean() * 100,
        analysis_df['delayed_disclosure'].mean() * 100,
        analysis_df['large_firm'].mean() * 100,
        (1 - analysis_df['large_firm'].mean()) * 100
    ]
})

composition.to_csv('outputs/essay2/tables/table2_sample_composition.csv', index=False)
print("\n✓ Table 2: Sample Composition")
print(composition)

# ============================================================
# SECTION 2: UNIVARIATE TESTS
# ============================================================

print("\n" + "=" * 60)
print("SECTION 2: UNIVARIATE ANALYSIS")
print("=" * 60)

# Table 3: CARs by Disclosure Timing
immediate = analysis_df[analysis_df['immediate_disclosure'] == 1]
delayed = analysis_df[analysis_df['delayed_disclosure'] == 1]

univariate_results = []

for var in ['car_5d', 'car_30d', 'bhar_5d', 'bhar_30d']:
    imm_mean = immediate[var].mean()
    imm_median = immediate[var].median()
    del_mean = delayed[var].mean()
    del_median = delayed[var].median()
    
    # T-test
    ttest = stats.ttest_ind(immediate[var].dropna(), delayed[var].dropna())
    
    # Mann-Whitney U test (non-parametric)
    mannwhitney = stats.mannwhitneyu(immediate[var].dropna(), delayed[var].dropna())
    
    univariate_results.append({
        'Variable': var,
        'Immediate_Mean': imm_mean,
        'Immediate_Median': imm_median,
        'Immediate_N': immediate[var].notna().sum(),
        'Delayed_Mean': del_mean,
        'Delayed_Median': del_median,
        'Delayed_N': delayed[var].notna().sum(),
        'Difference': imm_mean - del_mean,
        'T_Stat': ttest[0],
        'T_PValue': ttest[1],
        'MW_Stat': mannwhitney[0],
        'MW_PValue': mannwhitney[1]
    })

univariate_df = pd.DataFrame(univariate_results)
univariate_df.to_csv('outputs/essay2/tables/table3_univariate_disclosure.csv', index=False)
print("\n✓ Table 3: Univariate Tests - Disclosure Timing")
print(univariate_df.round(4))

# Table 4: CARs by FCC Status
fcc_reg = analysis_df[analysis_df['fcc_reportable'] == True]
non_fcc = analysis_df[analysis_df['fcc_reportable'] == False]

fcc_results = []

for var in ['car_5d', 'car_30d', 'bhar_5d', 'bhar_30d']:
    fcc_mean = fcc_reg[var].mean()
    fcc_median = fcc_reg[var].median()
    nonfcc_mean = non_fcc[var].mean()
    nonfcc_median = non_fcc[var].median()
    
    ttest = stats.ttest_ind(fcc_reg[var].dropna(), non_fcc[var].dropna())
    mannwhitney = stats.mannwhitneyu(fcc_reg[var].dropna(), non_fcc[var].dropna())
    
    fcc_results.append({
        'Variable': var,
        'FCC_Mean': fcc_mean,
        'FCC_Median': fcc_median,
        'FCC_N': fcc_reg[var].notna().sum(),
        'NonFCC_Mean': nonfcc_mean,
        'NonFCC_Median': nonfcc_median,
        'NonFCC_N': non_fcc[var].notna().sum(),
        'Difference': fcc_mean - nonfcc_mean,
        'T_Stat': ttest[0],
        'T_PValue': ttest[1],
        'MW_Stat': mannwhitney[0],
        'MW_PValue': mannwhitney[1]
    })

fcc_df = pd.DataFrame(fcc_results)
fcc_df.to_csv('outputs/essay2/tables/table4_univariate_fcc.csv', index=False)
print("\n✓ Table 4: Univariate Tests - FCC Status")
print(fcc_df.round(4))

# ============================================================
# SECTION 3: CORRELATION ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("SECTION 3: CORRELATION ANALYSIS")
print("=" * 60)

corr_vars = ['car_30d', 'immediate_disclosure', 'fcc_reportable', 
             'firm_size_log', 'leverage', 'roa', 'total_cves', 
             'cves_1yr_before', 'disclosure_delay_days']

corr_matrix = analysis_df[corr_vars].corr()
corr_matrix.to_csv('outputs/essay2/tables/table5_correlations.csv')

print("\n✓ Table 5: Correlation Matrix")
print(corr_matrix.round(3))

# Correlation heatmap
plt.figure(figsize=(12, 10))
sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0,
            square=True, linewidths=1)
plt.title('Correlation Matrix', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('outputs/essay2/figures/fig1_correlation_heatmap.png', dpi=300)
print("✓ Figure 1: Correlation Heatmap")

# ============================================================
# SECTION 4: MULTIVARIATE REGRESSION ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("SECTION 4: MULTIVARIATE REGRESSION")
print("=" * 60)

# Prepare regression data
reg_vars = ['car_30d', 'immediate_disclosure', 'fcc_reportable', 
            'firm_size_log', 'leverage', 'roa', 'total_cves']
reg_df = analysis_df[reg_vars].dropna()

print(f"\nRegression sample: n={len(reg_df)}")

# Model 1: Disclosure timing only
X1 = sm.add_constant(reg_df[['immediate_disclosure']])
y = reg_df['car_30d']
model1 = sm.OLS(y, X1).fit(cov_type='HC3')  # Robust standard errors

# Model 2: Add FCC regulation
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

# Model 5: Add CVE controls
X5 = sm.add_constant(reg_df[['immediate_disclosure', 'fcc_reportable', 'fcc_x_immediate',
                              'firm_size_log', 'leverage', 'total_cves']])
model5 = sm.OLS(y, X5).fit(cov_type='HC3')

# Create regression table
models = [model1, model2, model3, model4, model5]
model_names = ['Model 1', 'Model 2', 'Model 3', 'Model 4', 'Model 5']

reg_results = []
for i, model in enumerate(models):
    results_dict = {
        'Model': model_names[i],
        'N': int(model.nobs),
        'R²': model.rsquared,
        'Adj R²': model.rsquared_adj,
        'F-stat': model.fvalue
    }
    
    for var in model.params.index:
        if var != 'const':
            results_dict[f'{var}_coef'] = model.params[var]
            results_dict[f'{var}_se'] = model.bse[var]
            results_dict[f'{var}_pval'] = model.pvalues[var]
    
    reg_results.append(results_dict)

reg_results_df = pd.DataFrame(reg_results)
reg_results_df.to_csv('outputs/essay2/tables/table6_regression_results.csv', index=False)

print("\n✓ Table 6: Regression Results")
for i, model in enumerate(models):
    print(f"\n{model_names[i]}:")
    print(f"  N = {int(model.nobs)}, R² = {model.rsquared:.4f}")
    print(model.summary().tables[1])

# Save full regression output
with open('outputs/essay2/tables/regression_detailed_output.txt', 'w') as f:
    for i, model in enumerate(models):
        f.write(f"\n{'='*60}\n")
        f.write(f"{model_names[i]}\n")
        f.write(f"{'='*60}\n")
        f.write(str(model.summary()))
        f.write("\n\n")

# ============================================================
# SECTION 5: SUBSAMPLE ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("SECTION 5: SUBSAMPLE ANALYSIS")
print("=" * 60)

# By firm size
large_firms = reg_df[reg_df['firm_size_log'] > reg_df['firm_size_log'].median()]
small_firms = reg_df[reg_df['firm_size_log'] <= reg_df['firm_size_log'].median()]

print("\n--- Large Firms ---")
X_large = sm.add_constant(large_firms[['immediate_disclosure', 'fcc_reportable']])
model_large = sm.OLS(large_firms['car_30d'], X_large).fit(cov_type='HC3')
print(model_large.summary().tables[1])

print("\n--- Small Firms ---")
X_small = sm.add_constant(small_firms[['immediate_disclosure', 'fcc_reportable']])
model_small = sm.OLS(small_firms['car_30d'], X_small).fit(cov_type='HC3')
print(model_small.summary().tables[1])

# By CVE intensity
high_cve = reg_df[reg_df['total_cves'] > reg_df['total_cves'].median()]
low_cve = reg_df[reg_df['total_cves'] <= reg_df['total_cves'].median()]

print("\n--- High CVE Firms ---")
X_high = sm.add_constant(high_cve[['immediate_disclosure', 'fcc_reportable']])
model_high = sm.OLS(high_cve['car_30d'], X_high).fit(cov_type='HC3')
print(model_high.summary().tables[1])

print("\n--- Low CVE Firms ---")
X_low = sm.add_constant(low_cve[['immediate_disclosure', 'fcc_reportable']])
model_low = sm.OLS(low_cve['car_30d'], X_low).fit(cov_type='HC3')
print(model_low.summary().tables[1])

# Save subsample results
subsample_results = pd.DataFrame({
    'Subsample': ['Large Firms', 'Small Firms', 'High CVE', 'Low CVE'],
    'N': [len(large_firms), len(small_firms), len(high_cve), len(low_cve)],
    'Immediate_Coef': [
        model_large.params['immediate_disclosure'],
        model_small.params['immediate_disclosure'],
        model_high.params['immediate_disclosure'],
        model_low.params['immediate_disclosure']
    ],
    'Immediate_PVal': [
        model_large.pvalues['immediate_disclosure'],
        model_small.pvalues['immediate_disclosure'],
        model_high.pvalues['immediate_disclosure'],
        model_low.pvalues['immediate_disclosure']
    ],
    'FCC_Coef': [
        model_large.params['fcc_reportable'],
        model_small.params['fcc_reportable'],
        model_high.params['fcc_reportable'],
        model_low.params['fcc_reportable']
    ],
    'FCC_PVal': [
        model_large.pvalues['fcc_reportable'],
        model_small.pvalues['fcc_reportable'],
        model_high.pvalues['fcc_reportable'],
        model_low.pvalues['fcc_reportable']
    ]
})

subsample_results.to_csv('outputs/essay2/tables/table7_subsample_analysis.csv', index=False)
print("\n✓ Table 7: Subsample Analysis")

# ============================================================
# SECTION 6: ROBUSTNESS CHECKS
# ============================================================

print("\n" + "=" * 60)
print("SECTION 6: ROBUSTNESS CHECKS")
print("=" * 60)

# Robustness 1: Alternative dependent variables (BHAR, 5-day CAR)
print("\n--- Robustness 1: Alternative DVs ---")

# BHAR 30-day
X_robust = sm.add_constant(reg_df[['immediate_disclosure', 'fcc_reportable', 
                                    'firm_size_log', 'leverage', 'total_cves']])
model_bhar = sm.OLS(reg_df['bhar_30d'], X_robust).fit(cov_type='HC3')

# 5-day CAR
model_car5 = sm.OLS(reg_df['car_5d'], X_robust).fit(cov_type='HC3')

print("BHAR (30-day):")
print(model_bhar.summary().tables[1])
print("\nCAR (5-day):")
print(model_car5.summary().tables[1])

# Robustness 2: Winsorized returns (1st and 99th percentiles)
print("\n--- Robustness 2: Winsorized Returns ---")

from scipy.stats import mstats
reg_df['car_30d_winsor'] = mstats.winsorize(reg_df['car_30d'], limits=[0.01, 0.01])

model_winsor = sm.OLS(reg_df['car_30d_winsor'], X_robust).fit(cov_type='HC3')
print(model_winsor.summary().tables[1])

# Robustness 3: Alternative disclosure timing thresholds
print("\n--- Robustness 3: Alternative Thresholds ---")

# 14-day threshold
reg_df['immediate_14d'] = (reg_df['disclosure_delay_days'] <= 14).astype(int)
X_14d = sm.add_constant(reg_df[['immediate_14d', 'fcc_reportable', 
                                 'firm_size_log', 'leverage', 'total_cves']])
model_14d = sm.OLS(reg_df['car_30d'], X_14d).fit(cov_type='HC3')

print("14-day threshold:")
print(model_14d.summary().tables[1])

# Robustness 4: Year fixed effects
print("\n--- Robustness 4: Year Fixed Effects ---")

# Add year dummies (would need to extract year from breach_date in main df)
# This is a placeholder - implement if needed

# Save all robustness results
with open('outputs/essay2/robustness/robustness_checks.txt', 'w') as f:
    f.write("ROBUSTNESS CHECKS\n")
    f.write("="*60 + "\n\n")
    f.write("1. BHAR (30-day)\n")
    f.write(str(model_bhar.summary()))
    f.write("\n\n2. CAR (5-day)\n")
    f.write(str(model_car5.summary()))
    f.write("\n\n3. Winsorized Returns\n")
    f.write(str(model_winsor.summary()))
    f.write("\n\n4. 14-day Threshold\n")
    f.write(str(model_14d.summary()))

print("\n✓ Robustness checks saved")

# ============================================================
# SECTION 7: ADDITIONAL VISUALIZATIONS
# ============================================================

print("\n" + "=" * 60)
print("SECTION 7: VISUALIZATIONS")
print("=" * 60)

# Figure 2: CAR distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(analysis_df['car_5d'].dropna(), bins=50, edgecolor='black', alpha=0.7)
axes[0].axvline(x=0, color='r', linestyle='--', linewidth=2)
axes[0].set_xlabel('5-Day CAR (%)', fontsize=11)
axes[0].set_ylabel('Frequency', fontsize=11)
axes[0].set_title('Distribution of 5-Day CARs', fontsize=12, fontweight='bold')

axes[1].hist(analysis_df['car_30d'].dropna(), bins=50, edgecolor='black', alpha=0.7)
axes[1].axvline(x=0, color='r', linestyle='--', linewidth=2)
axes[1].set_xlabel('30-Day CAR (%)', fontsize=11)
axes[1].set_ylabel('Frequency', fontsize=11)
axes[1].set_title('Distribution of 30-Day CARs', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('outputs/essay2/figures/fig2_car_distributions.png', dpi=300)
print("✓ Figure 2: CAR Distributions")

# Figure 3: CAR by disclosure timing (box plots)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 5-day
data1 = [immediate['car_5d'].dropna(), delayed['car_5d'].dropna()]
bp1 = axes[0].boxplot(data1, labels=['Immediate', 'Delayed'], patch_artist=True)
for patch in bp1['boxes']:
    patch.set_facecolor('lightblue')
axes[0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[0].set_ylabel('5-Day CAR (%)', fontsize=11)
axes[0].set_title('5-Day CAR by Disclosure Timing', fontsize=12, fontweight='bold')
axes[0].grid(axis='y', alpha=0.3)

# 30-day
data2 = [immediate['car_30d'].dropna(), delayed['car_30d'].dropna()]
bp2 = axes[1].boxplot(data2, labels=['Immediate', 'Delayed'], patch_artist=True)
for patch in bp2['boxes']:
    patch.set_facecolor('lightgreen')
axes[1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[1].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[1].set_title('30-Day CAR by Disclosure Timing', fontsize=12, fontweight='bold')
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/essay2/figures/fig3_car_by_timing.png', dpi=300)
print("✓ Figure 3: CAR by Disclosure Timing")

# Figure 4: CAR by FCC status
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

data1 = [fcc_reg['car_30d'].dropna(), non_fcc['car_30d'].dropna()]
bp1 = axes[0].boxplot(data1, labels=['FCC-Regulated', 'Non-FCC'], patch_artist=True)
for patch in bp1['boxes']:
    patch.set_facecolor('coral')
axes[0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[0].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[0].set_title('CAR by Regulatory Status', fontsize=12, fontweight='bold')
axes[0].grid(axis='y', alpha=0.3)

# Interaction plot
immediate_fcc = analysis_df[(analysis_df['immediate_disclosure'] == 1) & (analysis_df['fcc_reportable'] == True)]
immediate_nonfcc = analysis_df[(analysis_df['immediate_disclosure'] == 1) & (analysis_df['fcc_reportable'] == False)]
delayed_fcc = analysis_df[(analysis_df['delayed_disclosure'] == 1) & (analysis_df['fcc_reportable'] == True)]
delayed_nonfcc = analysis_df[(analysis_df['delayed_disclosure'] == 1) & (analysis_df['fcc_reportable'] == False)]

means_fcc = [immediate_fcc['car_30d'].mean(), delayed_fcc['car_30d'].mean()]
means_nonfcc = [immediate_nonfcc['car_30d'].mean(), delayed_nonfcc['car_30d'].mean()]

axes[1].plot(['Immediate', 'Delayed'], means_fcc, marker='o', linewidth=2, label='FCC-Regulated', markersize=8)
axes[1].plot(['Immediate', 'Delayed'], means_nonfcc, marker='s', linewidth=2, label='Non-FCC', markersize=8)
axes[1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[1].set_ylabel('Mean 30-Day CAR (%)', fontsize=11)
axes[1].set_title('Interaction: Timing × FCC Status', fontsize=12, fontweight='bold')
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/essay2/figures/fig4_fcc_analysis.png', dpi=300)
print("✓ Figure 4: FCC Analysis")

# Figure 5: Scatter plot - Disclosure delay vs CAR
plt.figure(figsize=(10, 6))
plt.scatter(analysis_df['disclosure_delay_days'], analysis_df['car_30d'], alpha=0.5, s=30)
z = np.polyfit(analysis_df['disclosure_delay_days'].dropna(), 
               analysis_df.loc[analysis_df['disclosure_delay_days'].notna(), 'car_30d'], 1)
p = np.poly1d(z)
plt.plot(analysis_df['disclosure_delay_days'].sort_values(), 
         p(analysis_df['disclosure_delay_days'].sort_values()), 
         "r--", alpha=0.8, linewidth=2, label='Trend line')
plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
plt.xlabel('Disclosure Delay (days)', fontsize=12)
plt.ylabel('30-Day CAR (%)', fontsize=12)
plt.title('Relationship: Disclosure Delay and Market Reaction', fontsize=14, fontweight='bold')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('outputs/essay2/figures/fig5_delay_vs_car.png', dpi=300)
print("✓ Figure 5: Delay vs CAR")

# Figure 6: Time series of average CAR by year
analysis_df['breach_year'] = pd.to_datetime(analysis_df['breach_date']).dt.year
yearly_car = analysis_df.groupby('breach_year')['car_30d'].agg(['mean', 'count']).reset_index()

fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:blue'
ax1.set_xlabel('Year', fontsize=12)
ax1.set_ylabel('Mean 30-Day CAR (%)', color=color, fontsize=12)
ax1.plot(yearly_car['breach_year'], yearly_car['mean'], color=color, marker='o', linewidth=2, markersize=8)
ax1.tick_params(axis='y', labelcolor=color)
ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax1.grid(alpha=0.3)

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Number of Breaches', color=color, fontsize=12)
ax2.bar(yearly_car['breach_year'], yearly_car['count'], alpha=0.3, color=color)
ax2.tick_params(axis='y', labelcolor=color)

plt.title('Average CAR and Breach Frequency Over Time', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('outputs/essay2/figures/fig6_car_over_time.png', dpi=300)
print("✓ Figure 6: CAR Over Time")

# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("✓ COMPREHENSIVE ANALYSIS COMPLETE")
print("=" * 60)

print("\n📊 TABLES CREATED:")
print("  1. table1_descriptive_stats.csv")
print("  2. table2_sample_composition.csv")
print("  3. table3_univariate_disclosure.csv")
print("  4. table4_univariate_fcc.csv")
print("  5. table5_correlations.csv")
print("  6. table6_regression_results.csv")
print("  7. table7_subsample_analysis.csv")
print("  + regression_detailed_output.txt")

print("\n📈 FIGURES CREATED:")
print("  1. fig1_correlation_heatmap.png")
print("  2. fig2_car_distributions.png")
print("  3. fig3_car_by_timing.png")
print("  4. fig4_fcc_analysis.png")
print("  5. fig5_delay_vs_car.png")
print("  6. fig6_car_over_time.png")

print("\n🔬 ROBUSTNESS CHECKS:")
print("  - Alternative DVs (BHAR, 5-day CAR)")
print("  - Winsorized returns")
print("  - Alternative thresholds")
print("  - Subsample analysis (size, CVE intensity)")

print("\n" + "=" * 60)
print("All outputs saved in outputs/essay2/")
print("=" * 60)