import pandas as pd
import numpy as np
import wrds
from datetime import datetime

print("=" * 60)
print("SCRIPT 4: INSTITUTIONAL OWNERSHIP DATA")
print("=" * 60)

# Load breach data
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')
print(f"\n✓ Loaded {len(df)} breach records")

# Connect to WRDS
print("\nConnecting to WRDS...")
db = wrds.Connection()
print("✓ Connected")

# Get companies with PERMNO
analysis_df = df[df['PERMNO'].notna()].copy()
print(f"✓ {len(analysis_df)} records with PERMNO")

# Get unique PERMNOs
permnos = analysis_df['PERMNO'].dropna().unique().astype(int).tolist()
permno_list = ','.join([str(p) for p in permnos])

min_date = analysis_df['breach_date'].min() - pd.DateOffset(months=6)
max_date = analysis_df['breach_date'].max()

print(f"\nQuerying Thomson Reuters 13F data...")
print(f"Date range: {min_date.date()} to {max_date.date()}")
print(f"PERMNOs: {len(permnos)}")

try:
    # Query 13F institutional holdings
    # TR S34 contains institutional holdings data
    inst_holdings = db.raw_sql(f"""
        SELECT a.permno, a.fdate, a.shares, a.prc,
               b.shrout
        FROM tfn.s34 a
        LEFT JOIN crsp.msf b
        ON a.permno = b.permno 
        AND date_trunc('quarter', a.fdate) = date_trunc('quarter', b.date)
        WHERE a.permno IN ({permno_list})
        AND a.fdate >= '{min_date.strftime('%Y-%m-%d')}'
        AND a.fdate <= '{max_date.strftime('%Y-%m-%d')}'
    """)
    
    print(f"✓ Downloaded {len(inst_holdings)} institutional holding records")
    
    # Convert dates
    inst_holdings['fdate'] = pd.to_datetime(inst_holdings['fdate'])
    
    # Calculate institutional ownership metrics
    print("\nCalculating institutional ownership metrics...")
    
    # Aggregate by permno and quarter
    inst_holdings['quarter'] = inst_holdings['fdate'].dt.to_period('Q')
    
    inst_agg = inst_holdings.groupby(['permno', 'quarter']).agg({
        'shares': 'sum',  # Total shares held by institutions
        'shrout': 'first',  # Shares outstanding
        'fdate': 'first'
    }).reset_index()
    
    # Calculate ownership percentage
    inst_agg['inst_ownership_pct'] = (inst_agg['shares'] / (inst_agg['shrout'] * 1000)) * 100
    inst_agg['inst_ownership_pct'] = inst_agg['inst_ownership_pct'].clip(0, 100)  # Cap at 100%
    
    # Count number of institutional investors
    inst_count = inst_holdings.groupby(['permno', 'quarter']).size().reset_index(name='num_institutions')
    inst_agg = inst_agg.merge(inst_count, on=['permno', 'quarter'], how='left')
    
    # Match to breach dates
    print("\nMatching institutional ownership to breach dates...")
    
    results = []
    
    for idx, row in analysis_df.iterrows():
        permno = int(row['PERMNO'])
        breach_date = pd.to_datetime(row['breach_date'])
        breach_quarter = breach_date.to_period('Q')
        
        # Get most recent institutional ownership data before breach
        inst_data = inst_agg[
            (inst_agg['permno'] == permno) &
            (inst_agg['quarter'] <= breach_quarter)
        ].sort_values('quarter', ascending=False)
        
        if len(inst_data) > 0:
            recent = inst_data.iloc[0]
            
            inst_own_pct = recent['inst_ownership_pct']
            num_inst = recent['num_institutions']
            data_date = recent['fdate']
            
            # Calculate days between institutional data and breach
            days_lag = (breach_date - data_date).days
            
            # High institutional ownership dummy (>50%)
            high_inst_own = 1 if inst_own_pct > 50 else 0
            
            # Many institutions dummy (>20)
            many_institutions = 1 if num_inst > 20 else 0
            
        else:
            inst_own_pct = np.nan
            num_inst = 0
            data_date = pd.NaT
            days_lag = np.nan
            high_inst_own = 0
            many_institutions = 0
        
        results.append({
            'breach_id': idx,
            'PERMNO': permno,
            'breach_date': breach_date,
            'inst_ownership_pct': inst_own_pct,
            'num_institutions': num_inst,
            'high_institutional_ownership': high_inst_own,
            'many_institutions': many_institutions,
            'inst_data_date': data_date,
            'inst_data_lag_days': days_lag
        })
    
    results_df = pd.DataFrame(results)
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("INSTITUTIONAL OWNERSHIP SUMMARY")
    print("=" * 60)
    
    print(f"\nRecords with institutional data: {results_df['inst_ownership_pct'].notna().sum()} ({results_df['inst_ownership_pct'].notna().mean()*100:.1f}%)")
    print(f"Records with high inst. ownership (>50%): {results_df['high_institutional_ownership'].sum()}")
    
    print(f"\nInstitutional ownership % distribution:")
    print(results_df['inst_ownership_pct'].describe())
    
    print(f"\nNumber of institutions distribution:")
    print(results_df['num_institutions'].describe())
    
    print(f"\nTop 10 highest institutional ownership:")
    top_inst = results_df.nlargest(10, 'inst_ownership_pct')[['PERMNO', 'inst_ownership_pct', 'num_institutions']]
    print(top_inst.to_string(index=False))
    
    # Save results
    import os
    os.makedirs('Data/enrichment', exist_ok=True)
    
    results_df.to_csv('Data/enrichment/institutional_ownership.csv', index=False)
    print(f"\n✓ Saved to Data/enrichment/institutional_ownership.csv")
    
    print("\n" + "=" * 60)
    print("✓ SCRIPT 4 COMPLETE")
    print("=" * 60)
    print(f"\nCreated variables:")
    print("  • inst_ownership_pct")
    print("  • num_institutions")
    print("  • high_institutional_ownership")
    print("  • many_institutions")

except Exception as e:
    print(f"\n✗ Error querying Thomson Reuters data: {e}")
    print("\nThis may mean:")
    print("  1. Your WRDS subscription doesn't include Thomson Reuters 13F")
    print("  2. Table name may be different (check WRDS documentation)")
    print("  3. Permission issue")
    print("\nCreating placeholder file...")
    
    # Create placeholder
    results_df = pd.DataFrame({
        'breach_id': range(len(analysis_df)),
        'PERMNO': analysis_df['PERMNO'].values,
        'inst_ownership_pct': np.nan,
        'num_institutions': 0
    })
    
    results_df.to_csv('Data/enrichment/institutional_ownership.csv', index=False)
    print("✓ Created placeholder file")

finally:
    db.close()
    print("\n✓ WRDS connection closed")