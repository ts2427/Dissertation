import pandas as pd
import yfinance as yf
from datetime import timedelta
import time
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("ADDING STOCK PRICE DATA (ROBUST VERSION)")
print("=" * 60)

# Load master dataset
print("\n[1/3] Loading breach data...")
df = pd.read_excel('Data/processed/master_breach_dataset.xlsx')
print(f"✓ Loaded {len(df)} breach records")

# Get unique tickers
tickers = df['Map'].dropna().unique()
print(f"✓ Found {len(tickers)} unique stock tickers")

# Cache stock data to avoid repeated downloads
print("\n[2/3] Pre-downloading stock data for all tickers...")
print("This helps avoid rate limits and is faster overall...")

stock_cache = {}
failed_tickers = []

for i, ticker in enumerate(tickers, 1):
    try:
        if i % 10 == 0:
            print(f"  Downloading {i}/{len(tickers)} tickers...")
        
        stock = yf.Ticker(ticker)
        # Download all historical data at once
        hist = stock.history(period="max")
        
        if not hist.empty:
            # Remove timezone to avoid comparison issues
            hist.index = hist.index.tz_localize(None)
            stock_cache[ticker] = hist
        else:
            failed_tickers.append(ticker)
            
        time.sleep(0.1)  # Small delay to avoid rate limits
        
    except Exception as e:
        failed_tickers.append(ticker)
        continue

print(f"✓ Successfully downloaded data for {len(stock_cache)}/{len(tickers)} tickers")
if failed_tickers:
    print(f"  Failed tickers: {', '.join(failed_tickers[:10])}{'...' if len(failed_tickers) > 10 else ''}")

# Function to calculate stock returns
def get_breach_returns(ticker, breach_date):
    """
    Calculate stock returns before/after breach using cached data
    """
    try:
        # Get cached stock data
        if ticker not in stock_cache:
            return {
                'stock_price_at_breach': None,
                'return_5d_pct': None,
                'return_30d_pct': None,
                'has_stock_data': False
            }
        
        hist = stock_cache[ticker]
        
        # Ensure breach_date is timezone-naive
        if hasattr(breach_date, 'tz_localize'):
            breach_date = breach_date.tz_localize(None)
        elif hasattr(breach_date, 'tz') and breach_date.tz is not None:
            breach_date = breach_date.tz_localize(None)
        
        # Filter to dates around breach
        mask = (hist.index >= breach_date - timedelta(days=60)) & \
               (hist.index <= breach_date + timedelta(days=60))
        
        breach_window = hist[mask]
        
        if len(breach_window) < 10:
            return {
                'stock_price_at_breach': None,
                'return_5d_pct': None,
                'return_30d_pct': None,
                'has_stock_data': False
            }
        
        # Find closest date to breach
        time_diffs = abs(breach_window.index - breach_date)
        breach_idx = time_diffs.argmin()
        
        # Get indices for before/after periods
        # Pre-breach: look for trading day ~7 days before
        pre_mask = breach_window.index < breach_window.index[breach_idx]
        pre_data = breach_window[pre_mask]
        if len(pre_data) < 5:
            return {
                'stock_price_at_breach': None,
                'return_5d_pct': None,
                'return_30d_pct': None,
                'has_stock_data': False
            }
        pre_price = pre_data['Close'].iloc[-5] if len(pre_data) >= 5 else pre_data['Close'].iloc[0]
        
        # Post-breach: look for trading days ~5 and ~30 days after
        post_mask = breach_window.index > breach_window.index[breach_idx]
        post_data = breach_window[post_mask]
        
        if len(post_data) < 2:
            return {
                'stock_price_at_breach': None,
                'return_5d_pct': None,
                'return_30d_pct': None,
                'has_stock_data': False
            }
        
        # 5-day post (or closest available)
        post_5d_price = post_data['Close'].iloc[min(4, len(post_data)-1)]
        
        # 30-day post (or closest available)
        post_30d_price = post_data['Close'].iloc[min(20, len(post_data)-1)]
        
        # Breach day price
        breach_price = breach_window['Close'].iloc[breach_idx]
        
        # Calculate returns
        return_5d = ((post_5d_price - pre_price) / pre_price) * 100
        return_30d = ((post_30d_price - pre_price) / pre_price) * 100
        
        return {
            'stock_price_at_breach': round(float(breach_price), 2),
            'return_5d_pct': round(float(return_5d), 2),
            'return_30d_pct': round(float(return_30d), 2),
            'has_stock_data': True
        }
        
    except Exception as e:
        return {
            'stock_price_at_breach': None,
            'return_5d_pct': None,
            'return_30d_pct': None,
            'has_stock_data': False
        }

# Calculate returns for each breach
print("\n[3/3] Calculating returns for each breach...")

stock_metrics = []
successful = 0

for idx, row in df.iterrows():
    ticker = row['Map']
    breach_date = row['breach_date']
    
    if pd.isna(ticker) or pd.isna(breach_date):
        stock_metrics.append({
            'stock_price_at_breach': None,
            'return_5d_pct': None,
            'return_30d_pct': None,
            'has_stock_data': False
        })
        continue
    
    returns = get_breach_returns(ticker, breach_date)
    stock_metrics.append(returns)
    
    if returns['has_stock_data']:
        successful += 1
    
    if (idx + 1) % 100 == 0:
        print(f"  Processed {idx + 1}/{len(df)} records... ({successful} successful)")

print(f"  Final: {len(df)} records processed, {successful} with stock data")

# Add stock metrics to dataframe
stock_df = pd.DataFrame(stock_metrics)
df_final = pd.concat([df, stock_df], axis=1)

# Save final dataset
print("\nSaving final dataset...")
output_path = 'Data/processed/final_analysis_dataset.xlsx'
df_final.to_excel(output_path, index=False)
print(f"✓ Saved to: {output_path}")

# Summary statistics
print("\n" + "=" * 60)
print("STOCK DATA SUMMARY")
print("=" * 60)

total_with_ticker = df_final['Map'].notna().sum()
total_with_stock = stock_df['has_stock_data'].sum()

print(f"\nRecords with ticker: {total_with_ticker}")
print(f"Records with stock data: {total_with_stock}/{total_with_ticker} ({total_with_stock/total_with_ticker*100:.1f}%)")

# Return statistics
valid_returns = stock_df[stock_df['has_stock_data'] == True]

if len(valid_returns) > 0:
    print(f"\nStock return statistics (n={len(valid_returns)}):")
    print(f"  5-day return:")
    print(f"    Mean: {valid_returns['return_5d_pct'].mean():.2f}%")
    print(f"    Median: {valid_returns['return_5d_pct'].median():.2f}%")
    print(f"    Min: {valid_returns['return_5d_pct'].min():.2f}%")
    print(f"    Max: {valid_returns['return_5d_pct'].max():.2f}%")
    
    print(f"  30-day return:")
    print(f"    Mean: {valid_returns['return_30d_pct'].mean():.2f}%")
    print(f"    Median: {valid_returns['return_30d_pct'].median():.2f}%")
    print(f"    Min: {valid_returns['return_30d_pct'].min():.2f}%")
    print(f"    Max: {valid_returns['return_30d_pct'].max():.2f}%")
    
    # Negative returns
    neg_5d = (valid_returns['return_5d_pct'] < 0).sum()
    neg_30d = (valid_returns['return_30d_pct'] < 0).sum()
    print(f"\n  Breaches with negative returns:")
    print(f"    5-day: {neg_5d}/{len(valid_returns)} ({neg_5d/len(valid_returns)*100:.1f}%)")
    print(f"    30-day: {neg_30d}/{len(valid_returns)} ({neg_30d/len(valid_returns)*100:.1f}%)")

print("\n" + "=" * 60)
print("✓ FINAL DATASET COMPLETE")
print("=" * 60)
print("\nYour dataset is ready for:")
print("  - Correlation analysis (CVEs vs stock returns)")
print("  - Regression models (vulnerability impact on market reaction)")
print("  - Comparative analysis (high-CVE vs low-CVE companies)")