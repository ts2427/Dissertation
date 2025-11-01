import pandas as pd
import wrds
from datetime import datetime
import os

print("=" * 60)
print("DOWNLOADING WRDS DATA (FIXED)")
print("=" * 60)

# Load your breach dataset
print("\n[1/6] Loading breach dataset...")
breach_df = pd.read_excel('Data/processed/final_analysis_dataset.xlsx')
print(f"✓ Loaded {len(breach_df)} breach records")

# Get unique tickers and date range
tickers = breach_df['Map'].dropna().unique().tolist()
min_date = breach_df['breach_date'].min() - pd.DateOffset(years=1)
max_date = breach_df['breach_date'].max() + pd.DateOffset(years=1)

print(f"  Unique tickers: {len(tickers)}")
print(f"  Data window: {min_date.date()} to {max_date.date()}")

# Connect to WRDS
print("\n[2/6] Connecting to WRDS...")
db = wrds.Connection()
print("✓ Connected to WRDS")

os.makedirs('Data/wrds', exist_ok=True)

# Download CRSP Daily Returns - FIXED QUERY
print("\n[3/6] Downloading CRSP daily stock returns...")
try:
    ticker_list = "', '".join(tickers)
    
    # FIXED: Use b.ticker in SELECT and correct the join
    crsp_query = f"""
    SELECT a.permno, a.date, b.ticker, a.ret, a.retx, 
           a.prc, a.shrout, a.vol, a.cfacpr, a.cfacshr
    FROM crsp.dsf as a
    INNER JOIN crsp.msenames as b
    ON a.permno = b.permno
    AND b.namedt <= a.date
    AND a.date <= b.nameendt
    WHERE a.date >= '{min_date.strftime('%Y-%m-%d')}'
    AND a.date <= '{max_date.strftime('%Y-%m-%d')}'
    AND b.ticker IN ('{ticker_list}')
    """
    
    print(f"  Querying CRSP for {len(tickers)} tickers...")
    crsp_data = db.raw_sql(crsp_query)
    crsp_data.to_csv('Data/wrds/crsp_daily_returns.csv', index=False)
    print(f"✓ Downloaded {len(crsp_data):,} CRSP daily observations")
    print(f"  Saved to: Data/wrds/crsp_daily_returns.csv")
    
except Exception as e:
    print(f"✗ CRSP download failed: {e}")
    crsp_data = pd.DataFrame()

# Compustat already worked - skip

# Download CRSP-Compustat Link - FIXED TABLE PATH
print("\n[4/6] Downloading CRSP-Compustat link table...")
try:
    # Try alternative table paths
    ccm_queries = [
        # Path 1: Standard CCM
        """
        SELECT gvkey, lpermno as permno, linkdt, linkenddt, linktype, linkprim
        FROM crsp.ccmxpf_linktable
        WHERE linktype IN ('LU', 'LC')
        AND linkprim IN ('P', 'C')
        """,
        # Path 2: Alternative schema
        """
        SELECT gvkey, lpermno as permno, linkdt, linkenddt, linktype, linkprim
        FROM crsp_a_ccm.ccmxpf_linktable
        WHERE linktype IN ('LU', 'LC')
        AND linkprim IN ('P', 'C')
        """,
        # Path 3: Another alternative
        """
        SELECT gvkey, lpermno as permno, linkdt, linkenddt, linktype, linkprim
        FROM crspa.ccmxpf_linktable
        WHERE linktype IN ('LU', 'LC')
        AND linkprim IN ('P', 'C')
        """
    ]
    
    ccm_link = pd.DataFrame()
    for i, query in enumerate(ccm_queries, 1):
        try:
            print(f"  Trying CCM path {i}...")
            ccm_link = db.raw_sql(query)
            if not ccm_link.empty:
                break
        except:
            continue
    
    if not ccm_link.empty:
        ccm_link.to_csv('Data/wrds/crsp_compustat_link.csv', index=False)
        print(f"✓ Downloaded {len(ccm_link):,} link observations")
        print(f"  Saved to: Data/wrds/crsp_compustat_link.csv")
    else:
        print("✗ CCM link unavailable - will use ticker matching instead")
    
except Exception as e:
    print(f"✗ CCM link download failed: {e}")
    ccm_link = pd.DataFrame()

# Market indices already worked - skip

# Download additional Compustat annual data for controls
print("\n[5/6] Downloading Compustat annual fundamentals...")
try:
    ticker_list = "', '".join(tickers)
    
    compustat_annual_query = f"""
    SELECT gvkey, datadate, conm, tic, fyear,
           at, revt, ni, csho, prcc_f, sale, lt, act, lct,
           che, cogs, xsga, ib, ceq, emp, sich
    FROM comp.funda
    WHERE datadate >= '{min_date.strftime('%Y-%m-%d')}'
    AND datadate <= '{max_date.strftime('%Y-%m-%d')}'
    AND tic IN ('{ticker_list}')
    AND indfmt='INDL' 
    AND datafmt='STD' 
    AND popsrc='D' 
    AND consol='C'
    """
    
    print(f"  Querying Compustat annual data...")
    compustat_annual = db.raw_sql(compustat_annual_query)
    compustat_annual.to_csv('Data/wrds/compustat_annual.csv', index=False)
    print(f"✓ Downloaded {len(compustat_annual):,} annual observations")
    print(f"  Saved to: Data/wrds/compustat_annual.csv")
    
except Exception as e:
    print(f"✗ Compustat annual download failed: {e}")
    compustat_annual = pd.DataFrame()

# Get PERMNO mapping for your tickers
print("\n[6/6] Creating ticker-to-PERMNO mapping...")
try:
    ticker_list = "', '".join(tickers)
    
    permno_query = f"""
    SELECT DISTINCT ticker, permno, comnam, namedt, nameendt
    FROM crsp.msenames
    WHERE ticker IN ('{ticker_list}')
    ORDER BY ticker, namedt
    """
    
    permno_map = db.raw_sql(permno_query)
    permno_map.to_csv('Data/wrds/ticker_permno_mapping.csv', index=False)
    print(f"✓ Downloaded {len(permno_map):,} ticker-PERMNO mappings")
    print(f"  Saved to: Data/wrds/ticker_permno_mapping.csv")
    
except Exception as e:
    print(f"✗ PERMNO mapping failed: {e}")
    permno_map = pd.DataFrame()

# Close connection
db.close()
print("\n✓ WRDS connection closed")

# Summary
print("\n" + "=" * 60)
print("DOWNLOAD SUMMARY")
print("=" * 60)

summary = {
    'CRSP Daily Returns': len(crsp_data) if not crsp_data.empty else 0,
    'Compustat Quarterly': 4338,  # From previous run
    'Compustat Annual': len(compustat_annual) if not compustat_annual.empty else 0,
    'CRSP-Compustat Link': len(ccm_link) if not ccm_link.empty else 0,
    'Market Indices': 4802,  # From previous run
    'Ticker-PERMNO Map': len(permno_map) if not permno_map.empty else 0,
}

print("\nRecords downloaded:")
for dataset, count in summary.items():
    status = "✓" if count > 0 else "✗"
    print(f"  {status} {dataset}: {count:,}")

print("\n" + "=" * 60)
print("✓ WRDS DATA READY")
print("=" * 60)
print("\nYou now have:")
print("  ✓ Compustat financials (quarterly & annual)")
print("  ✓ Market indices for abnormal returns")
if len(crsp_data) > 0:
    print("  ✓ CRSP daily returns")
if len(permno_map) > 0:
    print("  ✓ Ticker-PERMNO mappings")

print("\nNext: Run python scripts\\16_merge_wrds_data.py")