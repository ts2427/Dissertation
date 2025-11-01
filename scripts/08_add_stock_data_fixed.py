import pandas as pd
import yfinance as yf
from datetime import timedelta
import time

print("=" * 60)
print("ADDING STOCK PRICE DATA (FIXED)")
print("=" * 60)

# Load master dataset
print("\n[1/3] Loading breach data...")
df = pd.read_excel('Data/processed/master_breach_dataset.xlsx')
print(f"✓ Loaded {len(df)} breach records")

# Get unique tickers
tickers = df['Map'].dropna().unique()
print(f"✓ Found {len(tickers)} unique stock tickers")

# Function to calculate stock returns around breach date
def get_breach_returns(ticker, breach_date, window_days=30):
    """
    Calculate stock returns before/after breach
    """
    try:
        # Convert breach_date to timezone-naive if it has timezone
        if hasattr(breach_date, 'tz') and breach_date.tz is not None:
            breach_date = breach_date.tz_localize(None)
        
        # Download stock data with extra buffer
        start_date = breach_date - timedelta(days=window_days + 20)
        end_date = breach_date + timedelta(days=window_days + 20)
        
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty or len(hist) < 10:
            return {
                'stock_price_at_breach': None,
                'return_5d_pct': None,
                'return_30d_pct': None,
                'has_stock_data': False
            }
        
        # Convert stock data index to timezone-naive
        hist.index = hist.index.tz_localize(None)
        
        # Find closest trading day to breach date
        breach_idx = (hist.index - breach_date).abs().argmin()
        
        # Ensure we have enough data before and after
        if breach_idx < 10 or breach_idx > len(hist) - 10:
            return {
                'stock_price_at_breach': None,
                'return_5d_pct': None,
                'return_30d_pct': None,
                'has_stock_data': False
            }
        
        # Price on/near breach date
        breach_price = hist.iloc[breach_idx]['Close']
        
        # Price ~5 trading days before (use 7 calendar days to be safe)
        pre_idx = max(0, breach_idx - 7)
        pre_price = hist.iloc[pre_idx]['Close']
        
        # Price ~5 trading days after
        post_5d_idx = min(len(hist) - 1, breach_idx + 7)
        post_5d_price = hist.iloc[post_5d_idx]['Close']
        
        # Price ~30 calendar days after
        post_30d_idx = min(len(hist) - 1, breach_idx + 30)
        post_30d_price = hist.iloc[post_30d_idx]['Close']
        
        # Calculate returns (% change from pre-breach price)
        return_5d = ((post_5d_price - pre_price) / pre_price) * 100
        return_30d = ((post_30d_price - pre_price) / pre_price) * 100
        
        return {
            'stock_price_at_breach': round(breach_price, 2),
            'return_5d_pct': round(return_5d, 2),
            'return_30d_pct': round(return_30d, 2),
            'has_stock_data': True
        }
        
    except Exception as e:
        # Silently handle errors - we'll see summary at end
        return {
            'stock_price_at_breach': None,
            'return_5d_pct': None,
            'return_30d_pct': None,
            'has_stock_data': False
        }

# Calculate returns for each breach
print("\n[2/3] Calculating stock returns around breach dates...")
print("This may take 5-10 minutes (processing quietly to reduce errors)...")

stock_metrics = []
processed = 0
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
    
    # Get stock returns
    returns = get_breach_returns(ticker, breach_date)
    stock_metrics.append(returns)
    
    if returns['has_stock_data']:
        successful += 1
    
    processed += 1
    if processed % 100 == 0:
        print(f"  Processed {processed}/{len(df)} records... ({successful} successful)")
        time.sleep(0.5)  # Rate limiting

print(f"  Final: {processed}/{len(df)} records processed, {successful} with stock data")

# Add stock metrics to dataframe
stock_df = pd.DataFrame(stock_metrics)
df_final = pd.concat([df, stock_df], axis=1)

# Save final dataset
print("\n[3/3] Saving final dataset...")
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

# Return statistics (only for successful fetches)
valid_returns = stock_df[stock_df['has_stock_data'] == True]

if len(valid_returns) > 0:
    print(f"\nStock return statistics (n={len(valid_returns)}):")
    print(f"  5-day return:")
    print(f"    Mean: {valid_returns['return_5d_pct'].mean():.2f}%")
    print(f"    Median: {valid_returns['return_5d_pct'].median():.2f}%")
    print(f"    Std Dev: {valid_returns['return_5d_pct'].std():.2f}%")
    print(f"  30-day return:")
    print(f"    Mean: {valid_returns['return_30d_pct'].mean():.2f}%")
    print(f"    Median: {valid_returns['return_30d_pct'].median():.2f}%")
    print(f"    Std Dev: {valid_returns['return_30d_pct'].std():.2f}%")
    
    # Negative returns (stock dropped)
    neg_5d = (valid_returns['return_5d_pct'] < 0).sum()
    neg_30d = (valid_returns['return_30d_pct'] < 0).sum()
    print(f"\n  Breaches with negative returns:")
    print(f"    5-day: {neg_5d}/{len(valid_returns)} ({neg_5d/len(valid_returns)*100:.1f}%)")
    print(f"    30-day: {neg_30d}/{len(valid_returns)} ({neg_30d/len(valid_returns)*100:.1f}%)")

print("\n" + "=" * 60)
print("✓ FINAL DATASET READY FOR ANALYSIS")
print("=" * 60)
print("\nDataset includes:")
print("  - Breach information (date, company, impact)")
print("  - CVE vulnerability counts (total, 1yr, 2yr, 5yr before)")
print("  - Stock returns (5-day and 30-day post-breach)")
print("\nReady for correlation and regression analysis!")