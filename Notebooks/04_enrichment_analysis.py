# %% [markdown]
# # Deep Dive: Enrichment Variables Analysis
# ## Prior Breaches, Severity, Turnover, Regulation, Dark Web

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')

# %%
df = pd.read_csv('../Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.csv')

print(f"Full Dataset: {len(df)} breaches")

# %% [markdown]
# ## 1. PRIOR BREACH HISTORY ANALYSIS

# %%
print("="*80)
print("PRIOR BREACH HISTORY")
print("="*80)

print(f"\nRepeat Offenders: {df['is_repeat_offender'].sum()} ({df['is_repeat_offender'].mean()*100:.1f}%)")
print(f"First-Time Breaches: {df['is_first_breach'].sum()} ({df['is_first_breach'].mean()*100:.1f}%)")
print(f"\nAverage prior breaches: {df['prior_breaches_total'].mean():.2f}")
print(f"Median prior breaches: {df['prior_breaches_total'].median():.0f}")
print(f"Max prior breaches: {df['prior_breaches_total'].max():.0f}")

# Distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(df['prior_breaches_total'], bins=50, color='steelblue', alpha=0.7, edgecolor='black')
axes[0].set_xlabel('Number of Prior Breaches', fontsize=11)
axes[0].set_ylabel('Frequency', fontsize=11)
axes[0].set_title('Distribution of Prior Breaches', fontsize=12, fontweight='bold')
axes[0].axvline(df['prior_breaches_total'].median(), color='red', linestyle='--', 
                label=f"Median: {df['prior_breaches_total'].median():.0f}")
axes[0].legend()
axes[0].grid(alpha=0.3)

# CARs by prior breach status
first_time_car = df[df['is_first_breach'] == 1]['car_30d'].dropna()
repeat_car = df[df['is_repeat_offender'] == 1]['car_30d'].dropna()

bp = axes[1].boxplot([first_time_car, repeat_car], labels=['First-Time', 'Repeat Offender'],
                      patch_artist=True)
bp['boxes'][0].set_facecolor('lightgreen')
bp['boxes'][1].set_facecolor('lightcoral')

axes[1].axhline(0, color='black', linestyle='-', linewidth=1)
axes[1].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[1].set_title('Market Reaction: First-Time vs Repeat Offenders', fontsize=12, fontweight='bold')
axes[1].grid(axis='y', alpha=0.3)

# Add means
axes[1].text(1, first_time_car.mean(), f'{first_time_car.mean():.2f}%', 
             ha='center', va='bottom', fontweight='bold')
axes[1].text(2, repeat_car.mean(), f'{repeat_car.mean():.2f}%', 
             ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('../outputs/figures/enrichment_prior_breaches.png', dpi=300, bbox_inches='tight')
plt.show()

# Statistical test
t_stat, p_val = stats.ttest_ind(first_time_car, repeat_car)
print(f"\nT-test: First-time vs Repeat Offenders")
print(f"  First-time mean CAR: {first_time_car.mean():.4f}%")
print(f"  Repeat offender mean CAR: {repeat_car.mean():.4f}%")
print(f"  Difference: {repeat_car.mean() - first_time_car.mean():.4f}%")
print(f"  t-statistic: {t_stat:.4f}")
print(f"  p-value: {p_val:.4f}")

# %% [markdown]
# ## 2. BREACH SEVERITY ANALYSIS

# %%
print("\n" + "="*80)
print("BREACH SEVERITY & TYPES")
print("="*80)

breach_types = {
    'PII Breach': df['pii_breach'].sum(),
    'Ransomware': df['ransomware'].sum(),
    'Financial Data': df['financial_breach'].sum(),
    'Health Data': df['health_breach'].sum(),
    'Insider Threat': df['insider_threat'].sum(),
    'Nation-State': df['nation_state'].sum()
}

for breach_type, count in breach_types.items():
    pct = (count / len(df)) * 100
    print(f"{breach_type:20} {count:4} ({pct:5.1f}%)")

# Severity distribution
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Breach types
types_df = pd.DataFrame(list(breach_types.items()), columns=['Type', 'Count'])
axes[0, 0].barh(types_df['Type'], types_df['Count'], color='steelblue', alpha=0.7)
axes[0, 0].set_xlabel('Number of Breaches', fontsize=11)
axes[0, 0].set_title('Breach Types (Non-Exclusive)', fontsize=12, fontweight='bold')
axes[0, 0].grid(axis='x', alpha=0.3)

# Plot 2: Severity score distribution
axes[0, 1].hist(df['combined_severity_score'], bins=30, color='darkred', alpha=0.7, edgecolor='black')
axes[0, 1].axvline(df['combined_severity_score'].median(), color='yellow', linestyle='--', linewidth=2,
                   label=f"Median: {df['combined_severity_score'].median():.1f}")
axes[0, 1].set_xlabel('Combined Severity Score', fontsize=11)
axes[0, 1].set_ylabel('Frequency', fontsize=11)
axes[0, 1].set_title('Distribution of Severity Scores', fontsize=12, fontweight='bold')
axes[0, 1].legend()
axes[0, 1].grid(alpha=0.3)

# Plot 3: CARs by severity
low_sev_car = df[df['high_severity_breach'] == 0]['car_30d'].dropna()
high_sev_car = df[df['high_severity_breach'] == 1]['car_30d'].dropna()

bp = axes[1, 0].boxplot([low_sev_car, high_sev_car], 
                         labels=['Low Severity', 'High Severity'],
                         patch_artist=True)
bp['boxes'][0].set_facecolor('lightblue')
bp['boxes'][1].set_facecolor('darkred')

axes[1, 0].axhline(0, color='black', linestyle='-', linewidth=1)
axes[1, 0].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[1, 0].set_title('Market Reaction by Severity', fontsize=12, fontweight='bold')
axes[1, 0].grid(axis='y', alpha=0.3)

# Plot 4: Health data breaches (HIPAA)
no_health_car = df[df['health_breach'] == 0]['car_30d'].dropna()
health_car = df[df['health_breach'] == 1]['car_30d'].dropna()

bp = axes[1, 1].boxplot([no_health_car, health_car], 
                         labels=['Non-Health', 'Health Data'],
                         patch_artist=True)
bp['boxes'][0].set_facecolor('lightgray')
bp['boxes'][1].set_facecolor('salmon')

axes[1, 1].axhline(0, color='black', linestyle='-', linewidth=1)
axes[1, 1].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[1, 1].set_title('Health Data Breaches (HIPAA)', fontsize=12, fontweight='bold')
axes[1, 1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('../outputs/figures/enrichment_severity.png', dpi=300, bbox_inches='tight')
plt.show()

# Statistical tests
print(f"\nSeverity Analysis:")
print(f"  Low severity mean CAR: {low_sev_car.mean():.4f}%")
print(f"  High severity mean CAR: {high_sev_car.mean():.4f}%")
print(f"  Difference: {high_sev_car.mean() - low_sev_car.mean():.4f}%")

t_stat, p_val = stats.ttest_ind(low_sev_car, high_sev_car)
print(f"  t-statistic: {t_stat:.4f}, p-value: {p_val:.4f}")

print(f"\nHealth Data Breaches:")
print(f"  Non-health mean CAR: {no_health_car.mean():.4f}%")
print(f"  Health data mean CAR: {health_car.mean():.4f}%")
print(f"  Difference: {health_car.mean() - no_health_car.mean():.4f}%")

t_stat, p_val = stats.ttest_ind(no_health_car, health_car)
print(f"  t-statistic: {t_stat:.4f}, p-value: {p_val:.4f}")

# %% [markdown]
# ## 3. EXECUTIVE TURNOVER ANALYSIS

# %%
print("\n" + "="*80)
print("EXECUTIVE TURNOVER")
print("="*80)

print(f"\nBreaches with executive turnover: {df['has_executive_change'].sum()} ({df['has_executive_change'].mean()*100:.1f}%)")
print(f"Average 8-K filings per breach: {df['num_8k_502'].mean():.2f}")

turnover_timing = df[df['has_executive_change'] == 1]['days_to_first_change'].dropna()
print(f"\nDays to first executive change:")
print(f"  Mean: {turnover_timing.mean():.1f} days")
print(f"  Median: {turnover_timing.median():.0f} days")
print(f"  25th percentile: {turnover_timing.quantile(0.25):.0f} days")
print(f"  75th percentile: {turnover_timing.quantile(0.75):.0f} days")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Turnover prevalence
turnover_counts = [df['has_executive_change'].sum(), 
                   len(df) - df['has_executive_change'].sum()]
axes[0, 0].pie(turnover_counts, labels=['Turnover', 'No Turnover'],
               autopct='%1.1f%%', colors=['lightcoral', 'lightgreen'],
               startangle=90)
axes[0, 0].set_title('Executive Turnover Within 1 Year', fontsize=12, fontweight='bold')

# Plot 2: Days to turnover distribution
axes[0, 1].hist(turnover_timing, bins=30, color='darkred', alpha=0.7, edgecolor='black')
axes[0, 1].axvline(turnover_timing.median(), color='yellow', linestyle='--', linewidth=2,
                   label=f"Median: {turnover_timing.median():.0f} days")
axes[0, 1].set_xlabel('Days to First Executive Change', fontsize=11)
axes[0, 1].set_ylabel('Frequency', fontsize=11)
axes[0, 1].set_title('Speed of Executive Accountability', fontsize=12, fontweight='bold')
axes[0, 1].legend()
axes[0, 1].grid(alpha=0.3)

# Plot 3: CARs by turnover
no_turnover_car = df[df['has_executive_change'] == 0]['car_30d'].dropna()
turnover_car = df[df['has_executive_change'] == 1]['car_30d'].dropna()

bp = axes[1, 0].boxplot([no_turnover_car, turnover_car],
                         labels=['No Turnover', 'Turnover'],
                         patch_artist=True)
bp['boxes'][0].set_facecolor('lightgreen')
bp['boxes'][1].set_facecolor('lightcoral')

axes[1, 0].axhline(0, color='black', linestyle='-', linewidth=1)
axes[1, 0].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[1, 0].set_title('Market Reaction by Executive Turnover', fontsize=12, fontweight='bold')
axes[1, 0].grid(axis='y', alpha=0.3)

# Plot 4: Number of 8-K filings
num_filings = df['num_8k_502'].value_counts().sort_index()
axes[1, 1].bar(num_filings.index[:20], num_filings.values[:20], color='steelblue', alpha=0.7)
axes[1, 1].set_xlabel('Number of 8-K Filings', fontsize=11)
axes[1, 1].set_ylabel('Number of Breaches', fontsize=11)
axes[1, 1].set_title('Distribution of 8-K Filings per Breach', fontsize=12, fontweight='bold')
axes[1, 1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('../outputs/figures/enrichment_executive_turnover.png', dpi=300, bbox_inches='tight')
plt.show()

# Statistical test
t_stat, p_val = stats.ttest_ind(no_turnover_car, turnover_car)
print(f"\nTurnover Effect on CARs:")
print(f"  No turnover mean CAR: {no_turnover_car.mean():.4f}%")
print(f"  Turnover mean CAR: {turnover_car.mean():.4f}%")
print(f"  Difference: {turnover_car.mean() - no_turnover_car.mean():.4f}%")
print(f"  t-statistic: {t_stat:.4f}, p-value: {p_val:.4f}")

# %% [markdown]
# ## 4. REGULATORY ENFORCEMENT ANALYSIS

# %%
print("\n" + "="*80)
print("REGULATORY ENFORCEMENT")
print("="*80)

print(f"\nBreaches with regulatory actions: {df['has_any_regulatory_action'].sum()} ({df['has_any_regulatory_action'].mean()*100:.1f}%)")
print(f"  FTC actions: {df['has_ftc_action'].sum()}")
print(f"  FCC actions: {df['has_fcc_action'].sum()}")
print(f"  State AG actions: {df['has_state_ag_action'].sum()}")

total_penalties = df['total_regulatory_cost'].sum()
print(f"\nTotal regulatory costs: ${total_penalties:,.0f}")
print(f"Mean penalty (if penalized): ${df[df['has_any_regulatory_action']==1]['total_regulatory_cost'].mean():,.0f}")
print(f"Median penalty (if penalized): ${df[df['has_any_regulatory_action']==1]['total_regulatory_cost'].median():,.0f}")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Types of regulatory actions
reg_types = pd.DataFrame({
    'Agency': ['FTC', 'FCC', 'State AG'],
    'Count': [df['has_ftc_action'].sum(), 
              df['has_fcc_action'].sum(), 
              df['has_state_ag_action'].sum()]
})

axes[0, 0].bar(reg_types['Agency'], reg_types['Count'], color=['darkred', 'navy', 'darkgreen'], alpha=0.7)
axes[0, 0].set_ylabel('Number of Actions', fontsize=11)
axes[0, 0].set_title('Regulatory Actions by Agency', fontsize=12, fontweight='bold')
axes[0, 0].grid(axis='y', alpha=0.3)

# Plot 2: Penalty distribution
penalties = df[df['total_regulatory_cost'] > 0]['total_regulatory_cost']
axes[0, 1].hist(penalties / 1_000_000, bins=20, color='darkred', alpha=0.7, edgecolor='black')
axes[0, 1].set_xlabel('Penalty Amount ($M)', fontsize=11)
axes[0, 1].set_ylabel('Frequency', fontsize=11)
axes[0, 1].set_title('Distribution of Regulatory Penalties', fontsize=12, fontweight='bold')
axes[0, 1].grid(alpha=0.3)

# Plot 3: CARs by regulatory action
no_reg_car = df[df['has_any_regulatory_action'] == 0]['car_30d'].dropna()
reg_car = df[df['has_any_regulatory_action'] == 1]['car_30d'].dropna()

bp = axes[1, 0].boxplot([no_reg_car, reg_car],
                         labels=['No Action', 'Regulatory Action'],
                         patch_artist=True)
bp['boxes'][0].set_facecolor('lightblue')
bp['boxes'][1].set_facecolor('darkred')

axes[1, 0].axhline(0, color='black', linestyle='-', linewidth=1)
axes[1, 0].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[1, 0].set_title('Market Reaction by Regulatory Status', fontsize=12, fontweight='bold')
axes[1, 0].grid(axis='y', alpha=0.3)

# Plot 4: Top 10 penalties
top_penalties = df.nlargest(10, 'total_regulatory_cost')[['org_name', 'total_regulatory_cost']].copy()
top_penalties['total_regulatory_cost'] = top_penalties['total_regulatory_cost'] / 1_000_000

axes[1, 1].barh(range(len(top_penalties)), top_penalties['total_regulatory_cost'], color='darkred', alpha=0.7)
axes[1, 1].set_yticks(range(len(top_penalties)))
axes[1, 1].set_yticklabels(top_penalties['org_name'], fontsize=9)
axes[1, 1].set_xlabel('Penalty ($M)', fontsize=11)
axes[1, 1].set_title('Top 10 Regulatory Penalties', fontsize=12, fontweight='bold')
axes[1, 1].grid(axis='x', alpha=0.3)
axes[1, 1].invert_yaxis()

plt.tight_layout()
plt.savefig('../outputs/figures/enrichment_regulatory.png', dpi=300, bbox_inches='tight')
plt.show()

# Statistical test
t_stat, p_val = stats.ttest_ind(no_reg_car, reg_car)
print(f"\nRegulatory Action Effect on CARs:")
print(f"  No action mean CAR: {no_reg_car.mean():.4f}%")
print(f"  Regulatory action mean CAR: {reg_car.mean():.4f}%")
print(f"  Difference: {reg_car.mean() - no_reg_car.mean():.4f}%")
print(f"  t-statistic: {t_stat:.4f}, p-value: {p_val:.4f}")

# %% [markdown]
# ## 5. DARK WEB PRESENCE ANALYSIS

# %%
print("\n" + "="*80)
print("DARK WEB PRESENCE (HIBP)")
print("="*80)

print(f"\nBreaches in HIBP database: {df['in_hibp'].sum()} ({df['in_hibp'].mean()*100:.1f}%)")

hibp_breaches = df[df['in_hibp'] == 1]
total_credentials = hibp_breaches['hibp_pwn_count'].sum()
print(f"Total credentials exposed: {total_credentials:,.0f}")
print(f"Mean credentials per breach: {hibp_breaches['hibp_pwn_count'].mean():,.0f}")
print(f"Median credentials per breach: {hibp_breaches['hibp_pwn_count'].median():,.0f}")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: HIBP presence
hibp_counts = [df['in_hibp'].sum(), len(df) - df['in_hibp'].sum()]
axes[0, 0].pie(hibp_counts, labels=['In HIBP', 'Not in HIBP'],
               autopct='%1.1f%%', colors=['darkred', 'lightgreen'],
               startangle=90)
axes[0, 0].set_title('Breaches in Dark Web (HIBP)', fontsize=12, fontweight='bold')

# Plot 2: Credentials compromised
if len(hibp_breaches) > 0:
    axes[0, 1].bar(range(len(hibp_breaches)), 
                   hibp_breaches['hibp_pwn_count'] / 1_000_000,
                   color='darkred', alpha=0.7)
    axes[0, 1].set_xlabel('Breach Index', fontsize=11)
    axes[0, 1].set_ylabel('Credentials Compromised (Millions)', fontsize=11)
    axes[0, 1].set_title('Scale of HIBP Breaches', fontsize=12, fontweight='bold')
    axes[0, 1].grid(axis='y', alpha=0.3)

# Plot 3: CARs by dark web presence
no_darkweb_car = df[df['in_hibp'] == 0]['car_30d'].dropna()
darkweb_car = df[df['in_hibp'] == 1]['car_30d'].dropna()

bp = axes[1, 0].boxplot([no_darkweb_car, darkweb_car],
                         labels=['Not in HIBP', 'In HIBP'],
                         patch_artist=True)
bp['boxes'][0].set_facecolor('lightgreen')
bp['boxes'][1].set_facecolor('darkred')

axes[1, 0].axhline(0, color='black', linestyle='-', linewidth=1)
axes[1, 0].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[1, 0].set_title('Market Reaction by Dark Web Presence', fontsize=12, fontweight='bold')
axes[1, 0].grid(axis='y', alpha=0.3)

# Plot 4: Top breaches by credentials
if len(hibp_breaches) > 0:
    top_hibp = hibp_breaches.nlargest(10, 'hibp_pwn_count')[['org_name', 'hibp_pwn_count']].copy()
    top_hibp['hibp_pwn_count'] = top_hibp['hibp_pwn_count'] / 1_000_000
    
    axes[1, 1].barh(range(len(top_hibp)), top_hibp['hibp_pwn_count'], color='darkred', alpha=0.7)
    axes[1, 1].set_yticks(range(len(top_hibp)))
    axes[1, 1].set_yticklabels(top_hibp['org_name'], fontsize=9)
    axes[1, 1].set_xlabel('Credentials (Millions)', fontsize=11)
    axes[1, 1].set_title('Top 10 Dark Web Breaches', fontsize=12, fontweight='bold')
    axes[1, 1].grid(axis='x', alpha=0.3)
    axes[1, 1].invert_yaxis()

plt.tight_layout()
plt.savefig('../outputs/figures/enrichment_darkweb.png', dpi=300, bbox_inches='tight')
plt.show()

# Statistical test
if len(darkweb_car) > 0:
    t_stat, p_val = stats.ttest_ind(no_darkweb_car, darkweb_car)
    print(f"\nDark Web Effect on CARs:")
    print(f"  Not in HIBP mean CAR: {no_darkweb_car.mean():.4f}%")
    print(f"  In HIBP mean CAR: {darkweb_car.mean():.4f}%")
    print(f"  Difference: {darkweb_car.mean() - no_darkweb_car.mean():.4f}%")
    print(f"  t-statistic: {t_stat:.4f}, p-value: {p_val:.4f}")

# %%
print("\n" + "="*80)
print("ENRICHMENT ANALYSIS COMPLETE!")
print("="*80)
print("\nAll enrichment visualizations saved to outputs/figures/")