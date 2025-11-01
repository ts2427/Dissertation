import pandas as pd
import numpy as np
import wrds

print("=" * 60)
print("SCRIPT 3: ANALYST COVERAGE DATA")
print("=" * 60)

# Load breach data
df = pd.read_excel('Data/processed/FINAL_DISSERTATION_DATASET.xlsx')
print(f"\n✓ Loaded {len(df)} breach records")

# Connect to WRDS
print("\nConnecting to WRDS...")
db = wrds.Connection()
print("✓ Connected")

# Get list of tickers and date ranges
analysis_df = df[df['Stock Ticker'].notna()].copy()
print(f"✓ {len(analysis_df)} records with stock tickers")

tickers = analysis_df['Stock Ticker'].dropna().unique().tolist()
ticker_list = ','.join([f"'{t}'" for t in tickers])

min_date = analysis_df['breach_date'].min() - pd.DateOffset(years=1)
max_date = analysis_df['breach_date'].max()

print(f"\nQuerying IBES for {len(tickers)} tickers...")
print(f"Date range: {min_date.date()} to {max_date.date()}")

# Query IBES Summary Statistics
# This contains number of analysts making estimates
try:
    analyst_data = db.raw_sql(f"""
        SELECT ticker, statpers, fpedats, numest, numup, numdown,
               meanest, medest, stdev, highest, lowest
        FROM ibes.statsum_epsus
        WHERE ticker IN ({ticker_list})
        AND statpers >= '{min_date.strftime('%Y-%m-%d')}'
        AND statpers <= '{max_date.strftime('%Y-%m-%d')}'
        AND fpi = '1'
        AND measure = 'EPS'
    """)
    
    print(f"✓ Downloaded {len(analyst_data)} analyst summary records")
    
    # Convert dates
    analyst_data['statpers'] = pd.to_datetime(analyst_data['statpers'])
    
    # For each breach, get analyst coverage metrics
    print("\nMatching analyst data to breach dates...")
    
    results = []
    
    for idx, row in analysis_df.iterrows():
        ticker = row['Stock Ticker']
        breach_date = pd.to_datetime(row['breach_date'])
        
        # Get analyst data closest to breach date (within 90 days before)
        window_start = breach_date - pd.DateOffset(days=90)
        window_end = breach_date
        
        analyst_window = analyst_data[
            (analyst_data['ticker'] == ticker) &
            (analyst_data['statpers'] >= window_start) &
            (analyst_data['statpers'] <= window_end)
        ].sort_values('statpers')
        
        if len(analyst_window) > 0:
            # Get most recent analyst summary
            recent = analyst_window.iloc[-1]
            
            num_analysts = recent['numest']
            num_upgrades = recent['numup']
            num_downgrades = recent['numdown']
            mean_estimate = recent['meanest']
            std_estimate = recent['stdev']
            
            # Calculate analyst coverage metrics
            high_coverage = 1 if num_analysts >= 5 else 0
            analyst_dispersion = std_estimate / abs(mean_estimate) if mean_estimate != 0 else np.nan
            
        else:
            num_analysts = 0
            num_upgrades = np.nan
            num_downgrades = np.nan
            mean_estimate = np.nan
            std_estimate = np.nan
            high_coverage = 0
            analyst_dispersion = np.nan
        
        results.append({
            'breach_id': idx,
            'ticker': ticker,
            'breach_date': breach_date,
            'num_analysts': num_analysts,
            'num_analyst_upgrades': num_upgrades,
            'num_analyst_downgrades': num_downgrades,
            'analyst_mean_estimate': mean_estimate,
            'analyst_std_estimate': std_estimate,
            'analyst_dispersion': analyst_dispersion,
            'high_analyst_coverage': high_coverage,
            'has_analyst_coverage': 1 if num_analysts > 0 else 0
        })
    
    results_df = pd.DataFrame(results)
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("ANALYST COVERAGE SUMMARY")
    print("=" * 60)
    
    print(f"\nRecords with analyst coverage: {results_df['has_analyst_coverage'].sum()} ({results_df['has_analyst_coverage'].mean()*100:.1f}%)")
    print(f"Records with high coverage (5+ analysts): {results_df['high_analyst_coverage'].sum()} ({results_df['high_analyst_coverage'].mean()*100:.1f}%)")
    
    print(f"\nAnalyst count distribution:")
    print(results_df['num_analysts'].describe())
    
    print(f"\nTop 10 most covered firms:")
    top_coverage = results_df.nlargest(10, 'num_analysts')[['ticker', 'num_analysts', 'breach_date']]
    print(top_coverage.to_string(index=False))
    
    # Save results
    import os
    os.makedirs('Data/enrichment', exist_ok=True)
    
    results_df.to_csv('Data/enrichment/analyst_coverage.csv', index=False)
    print(f"\n✓ Saved to Data/enrichment/analyst_coverage.csv")
    
    print("\n" + "=" * 60)
    print("✓ SCRIPT 3 COMPLETE")
    print("=" * 60)
    print(f"\nCreated variables:")
    print("  • num_analysts")
    print("  • num_analyst_upgrades")
    print("  • num_analyst_downgrades")
    print("  • analyst_mean_estimate")
    print("  • analyst_std_estimate")
    print("  • analyst_dispersion")
    print("  • high_analyst_coverage")
    print("  • has_analyst_coverage")

except Exception as e:
    print(f"\n✗ Error querying IBES: {e}")
    print("\nThis may mean:")
    print("  1. Your WRDS subscription doesn't include IBES")
    print("  2. IBES data not available for these tickers")
    print("  3. Date range issue")
    print("\nCreating placeholder file...")
    
    # Create placeholder
    results_df = pd.DataFrame({
        'breach_id': range(len(analysis_df)),
        'ticker': analysis_df['Stock Ticker'].values,
        'num_analysts': 0,
        'has_analyst_coverage': 0
    })
    
    results_df.to_csv('Data/enrichment/analyst_coverage.csv', index=False)
    print("✓ Created placeholder file")

finally:
    db.close()
    print("\n✓ WRDS connection closed")