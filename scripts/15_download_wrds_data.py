import pandas as pd
import wrds
from datetime import datetime
import os

print("=" * 60)
print("DOWNLOADING WRDS DATA")
print("=" * 60)

# Load your breach dataset
print("\n[1/8] Loading breach dataset...")
breach_df = pd.read_excel('Data/processed/final_analysis_dataset.xlsx')
print(f"✓ Loaded {len(breach_df)} breach records")
print(f"  Date range: {breach_df['breach_date'].min()} to {breach_df['breach_date'].max()}")

# Get unique tickers and date range
tickers = breach_df['Map'].dropna().unique().tolist()
min_date = breach_df['breach_date'].min() - pd.DateOffset(years=1)
max_date = breach_df['breach_date'].max() + pd.DateOffset(years=1)

print(f"\n  Unique tickers: {len(tickers)}")
print(f"  Data window: {min_date.date()} to {max_date.date()}")

# Connect to WRDS
print("\n[2/8] Connecting to WRDS...")
try:
    db = wrds.Connection()
    print("✓ Connected to WRDS")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("\nMake sure you have:")
    print("  1. WRDS account credentials")
    print("  2. wrds package installed: pip install wrds")
    print("  3. Configured credentials: import wrds; wrds.Connection(wrds_username='your_username')")
    exit()

# Create data directory
os.makedirs('Data/wrds', exist_ok=True)

# Download CRSP Daily Returns
print("\n[3/8] Downloading CRSP daily stock returns...")
try:
    # Create ticker list for SQL
    ticker_list = "', '".join(tickers)
    
    crsp_query = f"""
    SELECT a.permno, a.date, a.ticker, a.ret, a.retx, 
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

# Download Compustat Fundamentals
print("\n[4/8] Downloading Compustat fundamentals...")
try:
    ticker_list = "', '".join(tickers)
    
    compustat_query = f"""
    SELECT gvkey, datadate, conm, tic, fyearq, fqtr,
           atq, revtq, niq, cshoq, prccq, saleq, ltq, actq, lctq,
           cheq, cogsq, xsgaq, ibq, ceqq
    FROM comp.fundq
    WHERE datadate >= '{min_date.strftime('%Y-%m-%d')}'
    AND datadate <= '{max_date.strftime('%Y-%m-%d')}'
    AND tic IN ('{ticker_list}')
    """
    
    print(f"  Querying Compustat...")
    compustat_data = db.raw_sql(compustat_query)
    compustat_data.to_csv('Data/wrds/compustat_fundamentals.csv', index=False)
    print(f"✓ Downloaded {len(compustat_data):,} Compustat observations")
    print(f"  Saved to: Data/wrds/compustat_fundamentals.csv")
    
except Exception as e:
    print(f"✗ Compustat download failed: {e}")
    compustat_data = pd.DataFrame()

# Download CRSP-Compustat Link
print("\n[5/8] Downloading CRSP-Compustat link table...")
try:
    ccm_query = """
    SELECT gvkey, lpermno as permno, linkdt, linkenddt, linktype, linkprim
    FROM crsp.ccmxpf_linktable
    WHERE linktype IN ('LU', 'LC')
    AND linkprim IN ('P', 'C')
    """
    
    ccm_link = db.raw_sql(ccm_query)
    ccm_link.to_csv('Data/wrds/crsp_compustat_link.csv', index=False)
    print(f"✓ Downloaded {len(ccm_link):,} link observations")
    print(f"  Saved to: Data/wrds/crsp_compustat_link.csv")
    
except Exception as e:
    print(f"✗ CCM link download failed: {e}")
    ccm_link = pd.DataFrame()

# Download SOX 404 Internal Control Data
print("\n[6/8] Downloading SOX 404 internal control weaknesses...")
try:
    # Get CIK codes from breach data for matching
    cik_list = breach_df['CIK CODE'].dropna().unique().tolist()
    cik_str = ','.join([str(int(c)) for c in cik_list])
    
    sox_query = f"""
    SELECT company_fkey, fiscal_year_end, auditor_fkey,
           is404, ic_is_effective, 
           material_weakness_disclosed, auditor_opinion_key
    FROM audit.auditopinion
    WHERE fiscal_year_end >= '{min_date.strftime('%Y-%m-%d')}'
    AND fiscal_year_end <= '{max_date.strftime('%Y-%m-%d')}'
    """
    
    print(f"  Querying Audit Analytics...")
    sox_data = db.raw_sql(sox_query)
    sox_data.to_csv('Data/wrds/sox_internal_controls.csv', index=False)
    print(f"✓ Downloaded {len(sox_data):,} audit opinion observations")
    print(f"  Saved to: Data/wrds/sox_internal_controls.csv")
    
except Exception as e:
    print(f"✗ SOX data download failed: {e}")
    print(f"  Note: Requires Audit Analytics subscription")
    sox_data = pd.DataFrame()

# Download Financial Restatements
print("\n[7/8] Downloading financial restatements...")
try:
    restatement_query = f"""
    SELECT company_fkey, file_date, res_begin_date, res_end_date,
           res_accounting, res_adverse, res_fraud, res_sec_invest,
           restatement_key
    FROM audit.auditnonreli
    WHERE res_begin_date >= '{min_date.strftime('%Y-%m-%d')}'
    """
    
    restatements = db.raw_sql(restatement_query)
    restatements.to_csv('Data/wrds/financial_restatements.csv', index=False)
    print(f"✓ Downloaded {len(restatements):,} restatement observations")
    print(f"  Saved to: Data/wrds/financial_restatements.csv")
    
except Exception as e:
    print(f"✗ Restatement download failed: {e}")
    print(f"  Note: Requires Audit Analytics subscription")
    restatements = pd.DataFrame()

# Download Market Index Data (for abnormal returns)
print("\n[8/8] Downloading market index data...")
try:
    index_query = f"""
    SELECT date, vwretd, ewretd, sprtrn
    FROM crsp.dsi
    WHERE date >= '{min_date.strftime('%Y-%m-%d')}'
    AND date <= '{max_date.strftime('%Y-%m-%d')}'
    """
    
    market_data = db.raw_sql(index_query)
    market_data.to_csv('Data/wrds/market_indices.csv', index=False)
    print(f"✓ Downloaded {len(market_data):,} market index observations")
    print(f"  Saved to: Data/wrds/market_indices.csv")
    
except Exception as e:
    print(f"✗ Market data download failed: {e}")
    market_data = pd.DataFrame()

# Close connection
db.close()
print("\n✓ WRDS connection closed")

# Summary
print("\n" + "=" * 60)
print("DOWNLOAD SUMMARY")
print("=" * 60)

summary = {
    'CRSP Daily Returns': len(crsp_data) if not crsp_data.empty else 0,
    'Compustat Fundamentals': len(compustat_data) if not compustat_data.empty else 0,
    'CRSP-Compustat Link': len(ccm_link) if not ccm_link.empty else 0,
    'SOX Internal Controls': len(sox_data) if not sox_data.empty else 0,
    'Financial Restatements': len(restatements) if not restatements.empty else 0,
    'Market Indices': len(market_data) if not market_data.empty else 0,
}

print("\nRecords downloaded:")
for dataset, count in summary.items():
    status = "✓" if count > 0 else "✗"
    print(f"  {status} {dataset}: {count:,}")

print("\n" + "=" * 60)
print("NEXT STEPS")
print("=" * 60)
print("\n1. Run: python scripts/16_merge_wrds_data.py")
print("   - Merges WRDS data with breach dataset")
print("   - Creates control variables")
print("   - Calculates abnormal returns")
print("\n2. Data will be ready for:")
print("   - Event study analysis (abnormal returns)")
print("   - Regression models with firm controls")
print("   - Governance quality analysis")