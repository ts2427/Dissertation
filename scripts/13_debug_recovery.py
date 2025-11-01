import pandas as pd
import yfinance as yf
from datetime import timedelta

print("=" * 60)
print("DEBUGGING RECOVERY")
print("=" * 60)

# Load datasets
df_old = pd.read_excel('Data/processed/final_analysis_dataset.xlsx')
df_new = pd.read_excel('Data/processed/final_analysis_dataset_v2.xlsx')

# Check what changed
old_count = df_old['has_stock_data'].sum()
new_count = df_new['has_stock_data'].sum()

print(f"\nOld dataset: {old_count} with stock data")
print(f"New dataset: {new_count} with stock data")
print(f"Difference: {new_count - old_count}")

# Look at specific failed ticker that we recovered
print("\n" + "=" * 60)
print("EXAMINING UBER BREACHES")
print("=" * 60)

uber_breaches = df_new[df_new['Map'] == 'UBER'].copy()
print(f"\nFound {len(uber_breaches)} UBER breaches")
print(f"With stock data: {uber_breaches['has_stock_data'].sum()}")

print("\nBreach dates:")
for idx, row in uber_breaches.iterrows():
    print(f"  {row['breach_date']}: has_data={row['has_stock_data']}, return_5d={row['return_5d_pct']}")

# Let's manually try to get UBER data for one breach
if len(uber_breaches) > 0:
    sample_breach = uber_breaches.iloc[0]
    breach_date = sample_breach['breach_date']
    
    print(f"\n" + "=" * 60)
    print(f"MANUALLY TESTING UBER ON {breach_date}")
    print("=" * 60)
    
    try:
        stock = yf.Ticker('UBER')
        
        # Download with wider window
        start = breach_date - timedelta(days=90)
        end = breach_date + timedelta(days=90)
        
        print(f"Downloading: {start} to {end}")
        hist = stock.history(start=start, end=end)
        
        if not hist.empty:
            hist.index = hist.index.tz_localize(None)
            print(f"\n✓ Downloaded {len(hist)} days")
            print(f"Date range: {hist.index[0]} to {hist.index[-1]}")
            print(f"Breach date: {breach_date}")
            
            # Check if breach date is in range
            if breach_date >= hist.index[0] and breach_date <= hist.index[-1]:
                print("✓ Breach date IS in downloaded range")
                
                # Find closest date
                time_diffs = abs(hist.index - breach_date)
                closest_idx = time_diffs.argmin()
                closest_date = hist.index[closest_idx]
                
                print(f"Closest trading day: {closest_date}")
                print(f"Days difference: {abs((closest_date - breach_date).days)}")
                
                # Show surrounding prices
                window_start = max(0, closest_idx - 10)
                window_end = min(len(hist), closest_idx + 10)
                print(f"\nPrices around breach:")
                print(hist[['Close']].iloc[window_start:window_end])
                
            else:
                print("✗ Breach date is NOT in downloaded range")
                print(f"  Breach: {breach_date}")
                print(f"  Data starts: {hist.index[0]}")
                print(f"  Data ends: {hist.index[-1]}")
        else:
            print("✗ No data downloaded")
            
    except Exception as e:
        print(f"✗ Error: {e}")

# Check other recovered tickers
print("\n" + "=" * 60)
print("CHECKING OTHER RECOVERED TICKERS")
print("=" * 60)

recovered_tickers = ['HPE', 'FOXA', 'CHTR', 'GDDY', 'DELL', 'IHRT', 'META']

for ticker in recovered_tickers:
    ticker_breaches = df_new[df_new['Map'] == ticker]
    with_data = ticker_breaches['has_stock_data'].sum()
    total = len(ticker_breaches)
    
    print(f"{ticker}: {with_data}/{total} breaches with data")
    
    if with_data < total:
        # Show dates that don't have data
        missing = ticker_breaches[ticker_breaches['has_stock_data'] == False]
        print(f"  Missing dates: {missing['breach_date'].tolist()}")