# %% [markdown]
# # Essay 3: Disclosure Timing and Information Asymmetry
# ## Volatility Analysis with Governance Moderators

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.iolib.summary2 import summary_col
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')

# %%
# Load data
df = pd.read_csv('../Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.csv')

# Filter to Essay 3 sample (has volatility data)
essay3_df = df[
    (df['return_volatility_pre'].notna()) & 
    (df['return_volatility_post'].notna())
].copy()

# Create change variables
essay3_df['volatility_change_return'] = essay3_df['return_volatility_post'] - essay3_df['return_volatility_pre']
essay3_df['volatility_change_volume'] = essay3_df['volume_volatility_post'] - essay3_df['volume_volatility_pre']

print(f"Essay 3 Sample: {len(essay3_df)} breaches with volatility data")
print(f"Mean volatility change (return): {essay3_df['volatility_change_return'].mean():.6f}")

# %% [markdown]
# ## Hypothesis 1: Immediate Disclosure Reduces Information Asymmetry

# %%
# Model 1: Baseline Volatility Change
formula1 = """volatility_change_return ~ immediate_disclosure + fcc_reportable + 
              immediate_disclosure:fcc_reportable + firm_size_log + leverage + roa"""

model1_data = essay3_df.dropna(subset=['volatility_change_return', 'immediate_disclosure', 
                                        'fcc_reportable', 'firm_size_log', 'leverage', 'roa'])

model1 = smf.ols(formula=formula1, data=model1_data).fit(cov_type='HC3')

print("\n" + "="*80)
print("MODEL 1: BASELINE - Volatility Change")
print("="*80)
print(model1.summary())

# %% [markdown]
# ## Hypothesis 2: Governance Moderates Information Asymmetry

# %%
# Create governance composite
essay3_df['governance_score'] = (
    (essay3_df['firm_size_log'] - essay3_df['firm_size_log'].mean()) / essay3_df['firm_size_log'].std() +
    (essay3_df['leverage'] - essay3_df['leverage'].mean()) / essay3_df['leverage'].std() * -1 +  # Lower leverage = better
    (essay3_df['roa'] - essay3_df['roa'].mean()) / essay3_df['roa'].std()
) / 3

essay3_df['strong_governance'] = (essay3_df['governance_score'] > essay3_df['governance_score'].median()).astype(int)

# Model 2: Governance Interaction
formula2 = """volatility_change_return ~ immediate_disclosure + strong_governance + 
              immediate_disclosure:strong_governance + fcc_reportable + leverage + roa"""

model2_data = essay3_df.dropna(subset=['volatility_change_return', 'immediate_disclosure', 
                                        'strong_governance', 'fcc_reportable', 'leverage', 'roa'])

model2 = smf.ols(formula=formula2, data=model2_data).fit(cov_type='HC3')

print("\n" + "="*80)
print("MODEL 2: GOVERNANCE MODERATION")
print("="*80)
print(model2.summary())

# %% [markdown]
# ## Hypothesis 3: Prior Breaches as Governance Proxy

# %%
# Model 3: Prior Breaches Interaction
formula3 = """volatility_change_return ~ immediate_disclosure + is_repeat_offender + 
              immediate_disclosure:is_repeat_offender + fcc_reportable + 
              firm_size_log + leverage + roa"""

model3_data = essay3_df.dropna(subset=['volatility_change_return', 'immediate_disclosure', 
                                        'is_repeat_offender', 'fcc_reportable',
                                        'firm_size_log', 'leverage', 'roa'])

model3 = smf.ols(formula=formula3, data=model3_data).fit(cov_type='HC3')

print("\n" + "="*80)
print("MODEL 3: PRIOR BREACHES AS GOVERNANCE")
print("="*80)
print(model3.summary())

# %% [markdown]
# ## Hypothesis 4: Executive Turnover as Accountability Signal

# %%
# Model 4: Executive Turnover
formula4 = """volatility_change_return ~ immediate_disclosure + has_executive_change + 
              immediate_disclosure:has_executive_change + fcc_reportable + 
              firm_size_log + leverage + roa"""

model4_data = essay3_df.dropna(subset=['volatility_change_return', 'immediate_disclosure', 
                                        'has_executive_change', 'fcc_reportable',
                                        'firm_size_log', 'leverage', 'roa'])

model4 = smf.ols(formula=formula4, data=model4_data).fit(cov_type='HC3')

print("\n" + "="*80)
print("MODEL 4: EXECUTIVE TURNOVER")
print("="*80)
print(model4.summary())

# %% [markdown]
# ## Full Model: All Governance Proxies

# %%
# Model 5: Full Model
formula5 = """volatility_change_return ~ immediate_disclosure + strong_governance + 
              is_repeat_offender + has_executive_change + has_any_regulatory_action +
              fcc_reportable + firm_size_log + leverage + roa + high_severity_breach"""

model5_data = essay3_df.dropna(subset=['volatility_change_return', 'immediate_disclosure', 
                                        'strong_governance', 'is_repeat_offender',
                                        'has_executive_change', 'has_any_regulatory_action',
                                        'fcc_reportable', 'firm_size_log', 'leverage', 'roa',
                                        'high_severity_breach'])

model5 = smf.ols(formula=formula5, data=model5_data).fit(cov_type='HC3')

print("\n" + "="*80)
print("MODEL 5: FULL MODEL")
print("="*80)
print(model5.summary())

# %% [markdown]
# ## Table 4: Regression Results - Essay 3

# %%
models_list = [model1, model2, model3, model4, model5]
model_names = ['(1)\nBaseline', '(2)\nGovernance', '(3)\nPrior\nBreaches', 
               '(4)\nExec\nTurnover', '(5)\nFull']

reg_table = summary_col(models_list,
                         model_names=model_names,
                         stars=True,
                         float_format='%0.6f',
                         info_dict={
                             'N': lambda x: f"{int(x.nobs)}",
                             'R-squared': lambda x: f"{x.rsquared:.4f}"
                         })

print("\n" + "="*80)
print("TABLE 4: INFORMATION ASYMMETRY REGRESSIONS")
print("="*80)
print(reg_table)

# Save
with open('../outputs/tables/table4_essay3_regressions.tex', 'w') as f:
    f.write(reg_table.as_latex())

print("\n[OK] Table 4 saved")

# %% [markdown]
# ## Figure 5: Volatility Changes

# %%
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Pre vs Post Volatility
pre_vol = essay3_df['return_volatility_pre'].dropna()
post_vol = essay3_df['return_volatility_post'].dropna()

axes[0, 0].hist([pre_vol, post_vol], bins=30, label=['Pre-Breach', 'Post-Breach'], 
                alpha=0.7, color=['steelblue', 'coral'])
axes[0, 0].set_xlabel('Return Volatility', fontsize=11)
axes[0, 0].set_ylabel('Frequency', fontsize=11)
axes[0, 0].set_title('Return Volatility: Pre vs Post Breach', fontsize=12, fontweight='bold')
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3)

# Plot 2: Volatility Change by Disclosure
immediate_vol = essay3_df[essay3_df['immediate_disclosure'] == 1]['volatility_change_return'].dropna()
delayed_vol = essay3_df[essay3_df['delayed_disclosure'] == 1]['volatility_change_return'].dropna()

bp = axes[0, 1].boxplot([delayed_vol, immediate_vol], labels=['Delayed', 'Immediate'], 
                         patch_artist=True)
bp['boxes'][0].set_facecolor('lightcoral')
bp['boxes'][1].set_facecolor('lightgreen')

axes[0, 1].axhline(0, color='black', linestyle='--', linewidth=1)
axes[0, 1].set_ylabel('Volatility Change', fontsize=11)
axes[0, 1].set_title('Volatility Change by Disclosure Timing', fontsize=12, fontweight='bold')
axes[0, 1].grid(axis='y', alpha=0.3)

# Plot 3: By Governance
weak_gov = essay3_df[essay3_df['strong_governance'] == 0]['volatility_change_return'].dropna()
strong_gov = essay3_df[essay3_df['strong_governance'] == 1]['volatility_change_return'].dropna()

axes[1, 0].boxplot([weak_gov, strong_gov], labels=['Weak Gov', 'Strong Gov'])
axes[1, 0].axhline(0, color='black', linestyle='--', linewidth=1)
axes[1, 0].set_ylabel('Volatility Change', fontsize=11)
axes[1, 0].set_title('Volatility Change by Governance Quality', fontsize=12, fontweight='bold')
axes[1, 0].grid(axis='y', alpha=0.3)

# Plot 4: By Prior Breaches
first_vol = essay3_df[essay3_df['is_first_breach'] == 1]['volatility_change_return'].dropna()
repeat_vol = essay3_df[essay3_df['is_repeat_offender'] == 1]['volatility_change_return'].dropna()

axes[1, 1].boxplot([first_vol, repeat_vol], labels=['First-Time', 'Repeat'])
axes[1, 1].axhline(0, color='black', linestyle='--', linewidth=1)
axes[1, 1].set_ylabel('Volatility Change', fontsize=11)
axes[1, 1].set_title('Volatility Change by Prior Breach History', fontsize=12, fontweight='bold')
axes[1, 1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('../outputs/figures/fig5_volatility_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## Robustness: Volume Volatility

# %%
# Re-run with volume volatility
formula_vol = """volatility_change_volume ~ immediate_disclosure + strong_governance + 
                 immediate_disclosure:strong_governance + fcc_reportable + 
                 firm_size_log + leverage + roa"""

model_vol_data = essay3_df.dropna(subset=['volatility_change_volume', 'immediate_disclosure', 
                                           'strong_governance', 'fcc_reportable',
                                           'firm_size_log', 'leverage', 'roa'])

model_vol = smf.ols(formula=formula_vol, data=model_vol_data).fit(cov_type='HC3')

print("\n" + "="*80)
print("ROBUSTNESS: VOLUME VOLATILITY")
print("="*80)
print(model_vol.summary())

# %%
print("\n" + "="*80)
print("ESSAY 3 ANALYSIS COMPLETE!")
print("="*80)