import pandas as pd
import yfinance as yf
from datetime import timedelta
import time

print("=" * 60)
print("RECOVERING DELISTED STOCK DATA")
print("=" * 60)

# Load current dataset
df = pd.read_excel('Data/processed/final_analysis_dataset.xlsx')

# Find breaches that failed to get stock data
failed = df[(df['Map'].notna()) & (df['has_stock_data'] == False)].copy()
print(f"\n✓ Found {len(failed)} breaches without stock data")

if len(failed) == 0:
    print("All records already have stock data!")
    exit()

# Group by ticker to see which ones failed
failed_tickers = failed.groupby('Map').size().sort_values(ascending=False)
print(f"\nFailed tickers ({len(failed_tickers)} unique):")
for ticker, count in failed_tickers.head(15).items():
    print(f"  {ticker}: {count} breaches")

# Try alternative download methods for delisted stocks
print("\n" + "=" * 60)
print("ATTEMPTING ALTERNATIVE DOWNLOADS")
print("=" * 60)

recovered_data = {}
failed_permanently = []

for ticker in failed_tickers.index:
    print(f"\nTrying {ticker}...")
    
    try:
        # Method 1: Try with explicit date range from earliest breach
        ticker_breaches = failed[failed['Map'] == ticker]
        earliest_breach = ticker_breaches['breach_date'].min()
        latest_breach = ticker_breaches['breach_date'].max()
        
        # Download from well before first breach to well after last breach
        start = earliest_breach - timedelta(days=365)
        end = latest_breach + timedelta(days=365)
        
        stock = yf.Ticker(ticker)
        
        # Try downloading with specific date range
        hist = stock.history(start=start, end=end)
        
        if not hist.empty and len(hist) > 10:
            hist.index = hist.index.tz_localize(None)
            recovered_data[ticker] = hist
            print(f"  ✓ Recovered {len(hist)} days of data ({hist.index[0].date()} to {hist.index[-1].date()})")
        else:
            # Method 2: Try downloading ALL historical data
            print(f"  Trying full history download...")
            hist = stock.history(period="max", interval="1d")
            
            if not hist.empty and len(hist) > 10:
                hist.index = hist.index.tz_localize(None)
                recovered_data[ticker] = hist
                print(f"  ✓ Recovered {len(hist)} days of data (full history)")
            else:
                failed_permanently.append(ticker)
                print(f"  ✗ No data available")
        
        time.sleep(0.5)
        
    except Exception as e:
        failed_permanently.append(ticker)
        print(f"  ✗ Error: {str(e)[:60]}")

print(f"\n" + "=" * 60)
print("RECOVERY SUMMARY")
print("=" * 60)
print(f"Successfully recovered: {len(recovered_data)}/{len(failed_tickers)} tickers")
print(f"Permanently failed: {len(failed_permanently)}/{len(failed_tickers)} tickers")

if failed_permanently:
    print(f"\nPermanently unavailable tickers: {', '.join(failed_permanently)}")

# Now recalculate returns for recovered tickers
if len(recovered_data) > 0:
    print("\n" + "=" * 60)
    print("RECALCULATING RETURNS")
    print("=" * 60)
    
    def get_breach_returns(ticker, breach_date, hist):
        try:
            # Make breach_date timezone-naive
            if hasattr(breach_date, 'tz_localize'):
                breach_date = breach_date.tz_localize(None)
            elif hasattr(breach_date, 'tz') and breach_date.tz is not None:
                breach_date = breach_date.replace(tzinfo=None)
            
            # Get data around breach (±2 months)
            start = breach_date - timedelta(days=60)
            end = breach_date + timedelta(days=60)
            
            window = hist[(hist.index >= start) & (hist.index <= end)]
            
            if len(window) < 10:
                return None
            
            # Find closest trading day
            time_diffs = abs(window.index - breach_date)
            breach_idx = time_diffs.argmin()
            
            # Split into before/after
            before = window[window.index < window.index[breach_idx]]
            after = window[window.index >= window.index[breach_idx]]
            
            if len(before) < 5 or len(after) < 5:
                return None
            
            # Prices
            pre_price = before['Close'].iloc[-5]  # 5 days before
            breach_price = after['Close'].iloc[0]  # At breach
            post_5d = after['Close'].iloc[min(5, len(after)-1)]
            post_30d = after['Close'].iloc[min(20, len(after)-1)]
            
            # Calculate returns
            ret_5d = ((post_5d - pre_price) / pre_price) * 100
            ret_30d = ((post_30d - pre_price) / pre_price) * 100
            
            return {
                'stock_price_at_breach': round(float(breach_price), 2),
                'return_5d_pct': round(float(ret_5d), 2),
                'return_30d_pct': round(float(ret_30d), 2),
                'has_stock_data': True
            }
        except:
            return None
    
    # Update dataframe with recovered data
    updates_made = 0
    
    for idx, row in df.iterrows():
        # Only process rows that don't have stock data
        if row['has_stock_data'] == True:
            continue
        
        ticker = row['Map']
        breach_date = row['breach_date']
        
        if pd.isna(ticker) or pd.isna(breach_date) or ticker not in recovered_data:
            continue
        
        # Calculate returns using recovered data
        returns = get_breach_returns(ticker, breach_date, recovered_data[ticker])
        
        if returns:
            df.at[idx, 'stock_price_at_breach'] = returns['stock_price_at_breach']
            df.at[idx, 'return_5d_pct'] = returns['return_5d_pct']
            df.at[idx, 'return_30d_pct'] = returns['return_30d_pct']
            df.at[idx, 'has_stock_data'] = returns['has_stock_data']
            updates_made += 1
    
    print(f"\n✓ Updated {updates_made} breach records with recovered stock data")
    
    # Save updated dataset
    output_path = 'Data/processed/final_analysis_dataset_v2.xlsx'
    df.to_excel(output_path, index=False)
    print(f"✓ Saved updated dataset to: {output_path}")
    
    # New statistics
    with_stock = df['has_stock_data'].sum()
    with_ticker = df['Map'].notna().sum()
    
    print("\n" + "=" * 60)
    print("UPDATED DATASET SUMMARY")
    print("=" * 60)
    print(f"Total breach records: {len(df)}")
    print(f"Records with ticker: {with_ticker}")
    print(f"Records with stock data: {with_stock} ({with_stock/with_ticker*100:.1f}%)")
    print(f"Improvement: +{updates_made} records ({updates_made/with_ticker*100:.1f}% gain)")
    
else:
    print("\nNo data could be recovered. The tickers may be permanently unavailable.")