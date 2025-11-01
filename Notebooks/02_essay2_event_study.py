# %% [markdown]
# # Essay 2: Disclosure Timing and Market Reactions
# ## Event Study Analysis with Heterogeneity

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.iolib.summary2 import summary_col
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')

# %%
# Load data
df = pd.read_csv('../Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.csv')

# Filter to event study sample (has CRSP data)
essay2_df = df[df['has_crsp_data'] == True].copy()

print(f"Essay 2 Sample: {len(essay2_df)} breaches with CRSP data")
print(f"Mean CAR (30-day): {essay2_df['car_30d'].mean():.4f}%")

# %% [markdown]
# ## Hypothesis 1: Immediate Disclosure Reduces Negative CARs

# %%
def run_regression(df, dependent_var, model_name, controls=None):
    """Run OLS regression and return formatted results"""
    
    # Base specification
    formula = f"{dependent_var} ~ immediate_disclosure + fcc_reportable + immediate_disclosure:fcc_reportable"
    
    # Add controls if specified
    if controls:
        formula += " + " + " + ".join(controls)
    
    # Remove missing values
    model_data = df.dropna(subset=[dependent_var, 'immediate_disclosure', 'fcc_reportable'] + (controls or []))
    
    # Run regression
    model = smf.ols(formula=formula, data=model_data).fit(cov_type='HC3')  # Robust SE
    
    return model, len(model_data)

# Model 1: Baseline
controls_baseline = ['firm_size_log', 'leverage', 'roa']

model1, n1 = run_regression(essay2_df, 'car_30d', 'Baseline', controls_baseline)

print("\n" + "="*80)
print("MODEL 1: BASELINE - H1 (Immediate Disclosure)")
print("="*80)
print(model1.summary())

# %% [markdown]
# ## Hypothesis 2: Heterogeneity by Prior Breaches

# %%
# Model 2: Add Prior Breaches
controls_prior = controls_baseline + ['prior_breaches_total', 'is_repeat_offender']

model2, n2 = run_regression(essay2_df, 'car_30d', 'Prior Breaches', controls_prior)

print("\n" + "="*80)
print("MODEL 2: PRIOR BREACH EFFECTS")
print("="*80)
print(model2.summary())

# %% [markdown]
# ## Hypothesis 3: Heterogeneity by Breach Severity

# %%
# Model 3: Add Breach Severity
controls_severity = controls_baseline + ['high_severity_breach', 'ransomware', 'health_breach']

model3, n3 = run_regression(essay2_df, 'car_30d', 'Breach Severity', controls_severity)

print("\n" + "="*80)
print("MODEL 3: BREACH SEVERITY EFFECTS")
print("="*80)
print(model3.summary())

# %% [markdown]
# ## Hypothesis 4: Heterogeneity by Executive Turnover

# %%
# Model 4: Add Executive Turnover
controls_exec = controls_baseline + ['has_executive_change', 'days_to_first_change']

model4, n4 = run_regression(essay2_df, 'car_30d', 'Executive Turnover', controls_exec)

print("\n" + "="*80)
print("MODEL 4: EXECUTIVE TURNOVER EFFECTS")
print("="*80)
print(model4.summary())

# %% [markdown]
# ## Hypothesis 5: Heterogeneity by Regulatory Enforcement

# %%
# Model 5: Add Regulatory Enforcement
essay2_df['regulatory_penalty_millions'] = essay2_df['total_regulatory_cost'] / 1_000_000

controls_reg = controls_baseline + ['has_any_regulatory_action', 'regulatory_penalty_millions']

model5, n5 = run_regression(essay2_df, 'car_30d', 'Regulatory Enforcement', controls_reg)

print("\n" + "="*80)
print("MODEL 5: REGULATORY ENFORCEMENT EFFECTS")
print("="*80)
print(model5.summary())

# %% [markdown]
# ## Full Model: Kitchen Sink

# %%
# Model 6: All Enrichments
controls_full = controls_baseline + [
    'prior_breaches_total', 'high_severity_breach', 'ransomware',
    'has_executive_change', 'has_any_regulatory_action', 'in_hibp'
]

model6, n6 = run_regression(essay2_df, 'car_30d', 'Full Model', controls_full)

print("\n" + "="*80)
print("MODEL 6: FULL MODEL (ALL ENRICHMENTS)")
print("="*80)
print(model6.summary())

# %% [markdown]
# ## Table 3: Regression Results - Essay 2

# %%
# Create regression table
models_list = [model1, model2, model3, model4, model5, model6]
model_names = ['(1)\nBaseline', '(2)\nPrior\nBreaches', '(3)\nSeverity', 
               '(4)\nExec\nTurnover', '(5)\nRegulatory', '(6)\nFull']

reg_table = summary_col(models_list,
                         model_names=model_names,
                         stars=True,
                         float_format='%0.4f',
                         info_dict={
                             'N': lambda x: f"{int(x.nobs)}",
                             'R-squared': lambda x: f"{x.rsquared:.4f}",
                             'Adj. R-squared': lambda x: f"{x.rsquared_adj:.4f}"
                         })

print("\n" + "="*80)
print("TABLE 3: EVENT STUDY REGRESSIONS - 30-DAY CAR")
print("="*80)
print(reg_table)

# Save to LaTeX
with open('../outputs/tables/table3_essay2_regressions.tex', 'w') as f:
    f.write(reg_table.as_latex())

print("\n[OK] Table 3 saved to outputs/tables/")

# %% [markdown]
# ## Figure 4: Marginal Effects Plot

# %%
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
axes = axes.flatten()

# Plot 1: Immediate vs Delayed
immediate_cars = essay2_df[essay2_df['immediate_disclosure'] == 1]['car_30d'].dropna()
delayed_cars = essay2_df[essay2_df['delayed_disclosure'] == 1]['car_30d'].dropna()

axes[0].violinplot([delayed_cars, immediate_cars], positions=[1, 2], showmeans=True)
axes[0].set_xticks([1, 2])
axes[0].set_xticklabels(['Delayed', 'Immediate'])
axes[0].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[0].set_title('By Disclosure Timing', fontsize=12, fontweight='bold')
axes[0].axhline(0, color='red', linestyle='--', alpha=0.5)
axes[0].grid(axis='y', alpha=0.3)

# Plot 2: By Prior Breaches
first_time = essay2_df[essay2_df['is_first_breach'] == 1]['car_30d'].dropna()
repeat = essay2_df[essay2_df['is_repeat_offender'] == 1]['car_30d'].dropna()

axes[1].boxplot([first_time, repeat], labels=['First-Time', 'Repeat'])
axes[1].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[1].set_title('By Prior Breach History', fontsize=12, fontweight='bold')
axes[1].axhline(0, color='red', linestyle='--', alpha=0.5)
axes[1].grid(axis='y', alpha=0.3)

# Plot 3: By Severity
low_sev = essay2_df[essay2_df['high_severity_breach'] == 0]['car_30d'].dropna()
high_sev = essay2_df[essay2_df['high_severity_breach'] == 1]['car_30d'].dropna()

axes[2].boxplot([low_sev, high_sev], labels=['Low Severity', 'High Severity'])
axes[2].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[2].set_title('By Breach Severity', fontsize=12, fontweight='bold')
axes[2].axhline(0, color='red', linestyle='--', alpha=0.5)
axes[2].grid(axis='y', alpha=0.3)

# Plot 4: By Executive Turnover
no_turnover = essay2_df[essay2_df['has_executive_change'] == 0]['car_30d'].dropna()
has_turnover = essay2_df[essay2_df['has_executive_change'] == 1]['car_30d'].dropna()

axes[3].boxplot([no_turnover, has_turnover], labels=['No Turnover', 'Turnover'])
axes[3].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[3].set_title('By Executive Turnover', fontsize=12, fontweight='bold')
axes[3].axhline(0, color='red', linestyle='--', alpha=0.5)
axes[3].grid(axis='y', alpha=0.3)

# Plot 5: By Regulatory Action
no_reg = essay2_df[essay2_df['has_any_regulatory_action'] == 0]['car_30d'].dropna()
has_reg = essay2_df[essay2_df['has_any_regulatory_action'] == 1]['car_30d'].dropna()

axes[4].boxplot([no_reg, has_reg], labels=['No Action', 'Reg Action'])
axes[4].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[4].set_title('By Regulatory Enforcement', fontsize=12, fontweight='bold')
axes[4].axhline(0, color='red', linestyle='--', alpha=0.5)
axes[4].grid(axis='y', alpha=0.3)

# Plot 6: By Dark Web
no_darkweb = essay2_df[essay2_df['in_hibp'] == 0]['car_30d'].dropna()
in_darkweb = essay2_df[essay2_df['in_hibp'] == 1]['car_30d'].dropna()

axes[5].boxplot([no_darkweb, in_darkweb], labels=['Not in HIBP', 'In HIBP'])
axes[5].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[5].set_title('By Dark Web Presence', fontsize=12, fontweight='bold')
axes[5].axhline(0, color='red', linestyle='--', alpha=0.5)
axes[5].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('../outputs/figures/fig4_heterogeneity_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## Robustness: 5-Day CARs

# %%
# Re-run with 5-day CARs
model1_5d, _ = run_regression(essay2_df, 'car_5d', 'Baseline 5D', controls_baseline)
model6_5d, _ = run_regression(essay2_df, 'car_5d', 'Full 5D', controls_full)

print("\n" + "="*80)
print("ROBUSTNESS CHECK: 5-DAY CARs")
print("="*80)

robust_table = summary_col([model1_5d, model6_5d],
                            model_names=['(1) 5-Day\nBaseline', '(2) 5-Day\nFull'],
                            stars=True,
                            float_format='%0.4f')

print(robust_table)

# %% [markdown]
# ## Summary Statistics for Key Findings

# %%
print("\n" + "="*80)
print("KEY FINDINGS SUMMARY - ESSAY 2")
print("="*80)

# H1: Disclosure Timing
print("\nH1: Immediate Disclosure Effect")
print(f"  Coefficient: {model1.params['immediate_disclosure']:.4f}")
print(f"  p-value: {model1.pvalues['immediate_disclosure']:.4f}")
print(f"  Interpretation: Immediate disclosure {'reduces' if model1.params['immediate_disclosure'] < 0 else 'increases'} CAR by {abs(model1.params['immediate_disclosure']):.2f}%")

# Prior Breaches
print("\nPrior Breach Effect:")
if 'prior_breaches_total' in model2.params:
    print(f"  Coefficient: {model2.params['prior_breaches_total']:.4f}")
    print(f"  p-value: {model2.pvalues['prior_breaches_total']:.4f}")

# Severity
print("\nHigh Severity Effect:")
if 'high_severity_breach' in model3.params:
    print(f"  Coefficient: {model3.params['high_severity_breach']:.4f}")
    print(f"  p-value: {model3.pvalues['high_severity_breach']:.4f}")

# Executive Turnover
print("\nExecutive Turnover Effect:")
if 'has_executive_change' in model4.params:
    print(f"  Coefficient: {model4.params['has_executive_change']:.4f}")
    print(f"  p-value: {model4.pvalues['has_executive_change']:.4f}")

# Regulatory
print("\nRegulatory Action Effect:")
if 'has_any_regulatory_action' in model5.params:
    print(f"  Coefficient: {model5.params['has_any_regulatory_action']:.4f}")
    print(f"  p-value: {model5.pvalues['has_any_regulatory_action']:.4f}")

print("\n" + "="*80)
print("ESSAY 2 ANALYSIS COMPLETE!")
print("="*80)