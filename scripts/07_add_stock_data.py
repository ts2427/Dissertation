import pandas as pd
import yfinance as yf
from datetime import timedelta
import time

print("=" * 60)
print("ADDING STOCK PRICE DATA")
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
        # Download stock data
        start_date = breach_date - timedelta(days=window_days + 10)
        end_date = breach_date + timedelta(days=window_days + 10)
        
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            return None
        
        # Find prices around breach date
        breach_idx = hist.index.get_indexer([breach_date], method='nearest')[0]
        
        # Price on breach date
        breach_price = hist.iloc[breach_idx]['Close']
        
        # Price 5 days before
        pre_5d_idx = max(0, breach_idx - 5)
        pre_5d_price = hist.iloc[pre_5d_idx]['Close']
        
        # Price 5 days after
        post_5d_idx = min(len(hist) - 1, breach_idx + 5)
        post_5d_price = hist.iloc[post_5d_idx]['Close']
        
        # Price 30 days after
        post_30d_idx = min(len(hist) - 1, breach_idx + 30)
        post_30d_price = hist.iloc[post_30d_idx]['Close']
        
        # Calculate returns
        return_5d = ((post_5d_price - pre_5d_price) / pre_5d_price) * 100
        return_30d = ((post_30d_price - pre_5d_price) / pre_5d_price) * 100
        
        return {
            'stock_price_at_breach': breach_price,
            'return_5d_pct': return_5d,
            'return_30d_pct': return_30d,
            'has_stock_data': True
        }
        
    except Exception as e:
        print(f"  Error for {ticker}: {str(e)[:50]}")
        return {
            'stock_price_at_breach': None,
            'return_5d_pct': None,
            'return_30d_pct': None,
            'has_stock_data': False
        }

# Calculate returns for each breach
print("\n[2/3] Calculating stock returns around breach dates...")
print("This may take 5-10 minutes...")

stock_metrics = []
processed = 0

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
    
    processed += 1
    if processed % 50 == 0:
        print(f"  Processed {processed}/{len(df)} records...")
        time.sleep(1)  # Rate limiting

# Add stock metrics to dataframe
stock_df = pd.DataFrame(stock_metrics)
df_final = pd.concat([df, stock_df], axis=1)

# Save final dataset
print("\n[3/3] Saving final dataset...")
output_path = 'Data/processed/final_analysis_dataset.xlsx'
df_final.to_excel(output_path, index=False)
print(f"✓ Saved to: {output_path}")

# Summary
print("\n" + "=" * 60)
print("STOCK DATA SUMMARY")
print("=" * 60)
print(f"\nRecords with stock data: {stock_df['has_stock_data'].sum()}/{len(df)}")
print(f"\nAverage returns around breaches:")
print(f"  5-day return: {stock_df['return_5d_pct'].mean():.2f}%")
print(f"  30-day return: {stock_df['return_30d_pct'].mean():.2f}%")

print("\n" + "=" * 60)
print("✓ FINAL DATASET READY FOR ANALYSIS")
print("=" * 60)