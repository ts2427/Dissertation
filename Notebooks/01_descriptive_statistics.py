# %% [markdown]
# # Dissertation Analysis - Part 1: Descriptive Statistics
# ## Data Breach Disclosure Timing and Market Reactions

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# %%
# Load enriched dataset
df = pd.read_csv('../Data/processed/FINAL_DISSERTATION_DATASET_ENRICHED.csv')

print(f"Dataset loaded: {len(df)} breaches")
print(f"Variables: {len(df.columns)}")
print(f"Date range: {df['breach_date'].min()} to {df['breach_date'].max()}")

# %% [markdown]
# ## Table 1: Descriptive Statistics - Full Sample

# %%
def create_descriptive_stats(df, variables, var_names):
    """Create descriptive statistics table"""
    stats_list = []
    
    for var, name in zip(variables, var_names):
        if var not in df.columns:
            # Column doesn't exist
            stats_list.append({
                'Variable': name,
                'N': 0,
                'Mean': np.nan,
                'Std': np.nan,
                'Min': np.nan,
                'P25': '-',
                'Median': '-',
                'P75': '-',
                'Max': np.nan
            })
            continue
            
        data = df[var].dropna()
        
        # Skip if no data
        if len(data) == 0:
            stats_list.append({
                'Variable': name,
                'N': 0,
                'Mean': np.nan,
                'Std': np.nan,
                'Min': np.nan,
                'P25': '-',
                'Median': '-',
                'P75': '-',
                'Max': np.nan
            })
            continue
        
        # Check if numeric
        try:
            # Try to convert to numeric
            numeric_data = pd.to_numeric(data, errors='coerce').dropna()
            
            if len(numeric_data) == 0:
                # Not numeric data
                stats_list.append({
                    'Variable': name,
                    'N': len(data),
                    'Mean': '-',
                    'Std': '-',
                    'Min': '-',
                    'P25': '-',
                    'Median': '-',
                    'P75': '-',
                    'Max': '-'
                })
                continue
            
            # Check if binary/boolean
            unique_vals = set(numeric_data.unique())
            if unique_vals.issubset({0, 1, 0.0, 1.0}):
                # Binary column - show proportion
                stats_list.append({
                    'Variable': name,
                    'N': len(numeric_data),
                    'Mean': f"{numeric_data.mean():.3f}",
                    'Std': f"{numeric_data.std():.3f}",
                    'Min': int(numeric_data.min()),
                    'P25': '-',
                    'Median': '-',
                    'P75': '-',
                    'Max': int(numeric_data.max())
                })
            else:
                # Continuous column - show full stats
                stats_list.append({
                    'Variable': name,
                    'N': len(numeric_data),
                    'Mean': f"{numeric_data.mean():.3f}",
                    'Std': f"{numeric_data.std():.3f}",
                    'Min': f"{numeric_data.min():.3f}",
                    'P25': f"{numeric_data.quantile(0.25):.3f}",
                    'Median': f"{numeric_data.median():.3f}",
                    'P75': f"{numeric_data.quantile(0.75):.3f}",
                    'Max': f"{numeric_data.max():.3f}"
                })
                
        except Exception as e:
            # Any error - mark as non-numeric
            stats_list.append({
                'Variable': name,
                'N': len(data),
                'Mean': '-',
                'Std': '-',
                'Min': '-',
                'P25': '-',
                'Median': '-',
                'P75': '-',
                'Max': '-'
            })
    
    return pd.DataFrame(stats_list)

# Define variables for Table 1
variables = [
    # Dependent Variables
    'car_30d', 'bhar_30d', 'return_volatility_post',
    
    # Key Independent Variables
    'immediate_disclosure', 'delayed_disclosure', 'disclosure_delay_days',
    'fcc_reportable',
    
    # Firm Characteristics
    'firm_size_log', 'leverage', 'roa', 'total_affected',
    
    # Enrichments
    'prior_breaches_total', 'high_severity_breach', 
    'has_executive_change', 'total_regulatory_cost', 'in_hibp'
]

var_names = [
    'CAR (30-day, %)', 'BHAR (30-day, %)', 'Return Volatility (Post)',
    'Immediate Disclosure', 'Delayed Disclosure', 'Disclosure Delay (days)',
    'FCC Reportable',
    'Firm Size (log)', 'Leverage', 'ROA', 'Records Affected',
    'Prior Breaches', 'High Severity Breach', 
    'Executive Turnover', 'Regulatory Penalties ($M)', 'Dark Web Presence'
]

table1 = create_descriptive_stats(df, variables, var_names)

# Format for display
table1_display = table1.copy()
table1_display['Mean'] = table1_display['Mean'].apply(lambda x: f"{x:.3f}" if isinstance(x, (int, float)) and not pd.isna(x) else x)
table1_display['Std'] = table1_display['Std'].apply(lambda x: f"{x:.3f}" if isinstance(x, (int, float)) and not pd.isna(x) else x)
table1_display['Min'] = table1_display['Min'].apply(lambda x: f"{x:.3f}" if isinstance(x, (int, float)) and not pd.isna(x) else x)
table1_display['Max'] = table1_display['Max'].apply(lambda x: f"{x:.3f}" if isinstance(x, (int, float)) and not pd.isna(x) else x)

print("\n" + "="*80)
print("TABLE 1: DESCRIPTIVE STATISTICS")
print("="*80)
print(table1_display.to_string(index=False))

# Save
table1.to_csv('../outputs/tables/table1_descriptive_stats.csv', index=False)
table1.to_latex('../outputs/tables/table1_descriptive_stats.tex', index=False)

# %% [markdown]
# ## Table 2: Descriptive Statistics by Disclosure Timing

# %%
def compare_groups(df, group_var, variables, var_names):
    """Compare immediate vs delayed disclosure groups"""
    comparison_list = []
    
    for var, name in zip(variables, var_names):
        if var not in df.columns:
            continue
            
        # Get the two groups
        group0 = df[df[group_var] == 0][var].dropna()
        group1 = df[df[group_var] == 1][var].dropna()
        
        if len(group0) == 0 or len(group1) == 0:
            continue
        
        try:
            # Try to convert to numeric
            group0_numeric = pd.to_numeric(group0, errors='coerce').dropna()
            group1_numeric = pd.to_numeric(group1, errors='coerce').dropna()
            
            if len(group0_numeric) == 0 or len(group1_numeric) == 0:
                continue
            
            # Calculate statistics
            mean0 = group0_numeric.mean()
            mean1 = group1_numeric.mean()
            
            # T-test
            t_stat, p_val = stats.ttest_ind(group0_numeric, group1_numeric, equal_var=False)
            
            comparison_list.append({
                'Variable': name,
                'Delayed Mean': f"{mean0:.3f}",
                'Immediate Mean': f"{mean1:.3f}",
                'Difference': f"{mean1 - mean0:.3f}",
                't-stat': f"{t_stat:.3f}",
                'p-value': f"{p_val:.3f}",
                'Sig': '***' if p_val < 0.01 else '**' if p_val < 0.05 else '*' if p_val < 0.10 else ''
            })
            
        except Exception as e:
            # Skip variables that cause errors
            continue
    
    return pd.DataFrame(comparison_list)

table2 = compare_groups(df, 'immediate_disclosure', variables, var_names)

print("\nTable 2: Univariate Comparison - Immediate vs. Delayed Disclosure")
print("="*80)
print(table2.to_string(index=False))

table2.to_csv('../outputs/tables/table2_univariate_comparison.csv', index=False)

# %% [markdown]
# ## Figure 1: Timeline of Breaches

# %%
# Convert breach_date to datetime
df['breach_date'] = pd.to_datetime(df['breach_date'])
df['breach_year'] = df['breach_date'].dt.year

# Count by year
breach_timeline = df.groupby('breach_year').size().reset_index(name='count')

fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(breach_timeline['breach_year'], breach_timeline['count'], color='steelblue', alpha=0.7)
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Breaches', fontsize=12)
ax.set_title('Timeline of Data Breaches (2004-2025)', fontsize=14, fontweight='bold')
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('../outputs/figures/fig1_breach_timeline.png', dpi=300, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## Figure 2: Distribution of CARs

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# CAR distribution
axes[0].hist(df['car_30d'].dropna(), bins=50, color='steelblue', alpha=0.7, edgecolor='black')
axes[0].axvline(df['car_30d'].mean(), color='red', linestyle='--', linewidth=2, label=f"Mean: {df['car_30d'].mean():.2f}%")
axes[0].axvline(0, color='black', linestyle='-', linewidth=1)
axes[0].set_xlabel('30-Day CAR (%)', fontsize=11)
axes[0].set_ylabel('Frequency', fontsize=11)
axes[0].set_title('Distribution of 30-Day CARs', fontsize=12, fontweight='bold')
axes[0].legend()
axes[0].grid(alpha=0.3)

# CAR by disclosure timing
immediate = df[df['immediate_disclosure'] == 1]['car_30d'].dropna()
delayed = df[df['delayed_disclosure'] == 1]['car_30d'].dropna()

bp = axes[1].boxplot([delayed, immediate], labels=['Delayed', 'Immediate'], 
                      patch_artist=True, widths=0.6)
bp['boxes'][0].set_facecolor('lightcoral')
bp['boxes'][1].set_facecolor('lightgreen')

axes[1].axhline(0, color='black', linestyle='-', linewidth=1)
axes[1].set_ylabel('30-Day CAR (%)', fontsize=11)
axes[1].set_title('CARs by Disclosure Timing', fontsize=12, fontweight='bold')
axes[1].grid(axis='y', alpha=0.3)

# Add means
axes[1].text(1, delayed.mean(), f'{delayed.mean():.2f}%', ha='center', va='bottom', fontweight='bold')
axes[1].text(2, immediate.mean(), f'{immediate.mean():.2f}%', ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('../outputs/figures/fig2_car_distribution.png', dpi=300, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## Figure 3: Enrichment Highlights

# %%
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Prior breaches
axes[0, 0].pie([df['is_first_breach'].sum(), df['is_repeat_offender'].sum()],
               labels=['First-Time\nBreaches', 'Repeat\nOffenders'],
               autopct='%1.1f%%',
               colors=['lightblue', 'salmon'],
               startangle=90)
axes[0, 0].set_title('Prior Breach History', fontsize=12, fontweight='bold')

# Breach severity
severity_counts = df[['pii_breach', 'ransomware', 'health_breach', 'financial_breach']].sum()
axes[0, 1].bar(range(len(severity_counts)), severity_counts.values, color='steelblue', alpha=0.7)
axes[0, 1].set_xticks(range(len(severity_counts)))
axes[0, 1].set_xticklabels(['PII', 'Ransomware', 'Health', 'Financial'], rotation=45)
axes[0, 1].set_ylabel('Number of Breaches', fontsize=11)
axes[0, 1].set_title('Breach Types', fontsize=12, fontweight='bold')
axes[0, 1].grid(axis='y', alpha=0.3)

# Executive turnover
turnover_data = [df['has_executive_change'].sum(), len(df) - df['has_executive_change'].sum()]
axes[1, 0].pie(turnover_data,
               labels=['Executive\nTurnover', 'No\nTurnover'],
               autopct='%1.1f%%',
               colors=['lightcoral', 'lightgreen'],
               startangle=90)
axes[1, 0].set_title('Executive Turnover Within 1 Year', fontsize=12, fontweight='bold')

# Regulatory enforcement
reg_counts = df[['has_ftc_action', 'has_fcc_action', 'has_state_ag_action']].sum()
axes[1, 1].bar(range(len(reg_counts)), reg_counts.values, color='darkred', alpha=0.7)
axes[1, 1].set_xticks(range(len(reg_counts)))
axes[1, 1].set_xticklabels(['FTC', 'FCC', 'State AG'])
axes[1, 1].set_ylabel('Number of Actions', fontsize=11)
axes[1, 1].set_title('Regulatory Enforcement Actions', fontsize=12, fontweight='bold')
axes[1, 1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('../outputs/figures/fig3_enrichment_highlights.png', dpi=300, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## Correlation Matrix

# %%
# Select key variables for correlation
corr_vars = ['car_30d', 'immediate_disclosure', 'fcc_reportable', 
             'firm_size_log', 'prior_breaches_total', 'high_severity_breach',
             'has_executive_change', 'has_any_regulatory_action']

corr_data = df[corr_vars].corr()

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_data, annot=True, fmt='.3f', cmap='coolwarm', center=0,
            square=True, linewidths=1, cbar_kws={"shrink": 0.8})
ax.set_title('Correlation Matrix - Key Variables', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('../outputs/figures/correlation_matrix.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nCorrelation saved!")

# %%
print("\n" + "="*80)
print("DESCRIPTIVE STATISTICS COMPLETE!")
print("="*80)
print("\nGenerated:")
print("  [OK] Table 1: Descriptive Statistics")
print("  [OK] Table 2: Univariate Comparison")
print("  [OK] Figure 1: Breach Timeline")
print("  [OK] Figure 2: CAR Distribution")
print("  [OK] Figure 3: Enrichment Highlights")
print("  [OK] Correlation Matrix")