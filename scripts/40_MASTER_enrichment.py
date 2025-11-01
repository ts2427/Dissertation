import subprocess
import time
import os

print("=" * 80)
print(" " * 20 + "MASTER DATA ENRICHMENT PIPELINE")
print("=" * 80)

print("\nThis script will run all 10 data enrichment scripts automatically.")
print("Total estimated time: 30-45 minutes")
print("\nPress Enter to start, or Ctrl+C to cancel...")
input()

# Define all enrichment scripts in order
pipelines = [
    {
        'number': 1,
        'name': 'Prior Breach History',
        'script': '41_prior_breaches.py',
        'est_time': '1 minute',
        'description': 'Count repeat offenders and breach frequency'
    },
    {
        'number': 2,
        'name': 'Industry-Adjusted Returns',
        'script': '42_industry_returns.py',
        'est_time': '3 minutes',
        'description': 'Calculate industry-adjusted CARs from WRDS'
    },
    {
        'number': 3,
        'name': 'Analyst Coverage',
        'script': '43_analyst_coverage.py',
        'est_time': '2 minutes',
        'description': 'Get analyst coverage from IBES'
    },
    {
        'number': 4,
        'name': 'Institutional Ownership',
        'script': '44_institutional_ownership.py',
        'est_time': '3 minutes',
        'description': 'Get institutional ownership from Thomson Reuters 13F'
    },
    {
        'number': 5,
        'name': 'Breach Severity Classification',
        'script': '45_breach_severity_nlp.py',
        'est_time': '2 minutes',
        'description': 'NLP classification of breach types and severity'
    },
    {
        'number': 6,
        'name': 'Executive Turnover',
        'script': '46_executive_changes.py',
        'est_time': '10 minutes',
        'description': 'Detect executive changes from SEC 8-K filings'
    },
    {
        'number': 7,
        'name': 'Regulatory Enforcement',
        'script': '47_regulatory_enforcement.py',
        'est_time': '1 minute',
        'description': 'Check FTC/FCC enforcement actions'
    },
    {
        'number': 8,
        'name': 'Dark Web Presence',
        'script': '48_dark_web_check.py',
        'est_time': '5 minutes',
        'description': 'Check if breach data in HIBP database'
    },
    {
        'number': 9,
        'name': 'Media Coverage',
        'script': '49_media_coverage.py',
        'est_time': '15 minutes',
        'description': 'Get news coverage from GDELT'
    },
    {
        'number': 10,
        'name': 'Cyber Insurance',
        'script': '50_cyber_insurance.py',
        'est_time': '5 minutes',
        'description': 'Detect cyber insurance disclosures in 10-Ks'
    }
]

# Track results
results = []
start_time = time.time()

print("\n" + "=" * 80)
print("STARTING ENRICHMENT PIPELINE")
print("=" * 80)

for pipeline in pipelines:
    print("\n" + "=" * 80)
    print(f"SCRIPT {pipeline['number']}/10: {pipeline['name']}")
    print("=" * 80)
    print(f"Description: {pipeline['description']}")
    print(f"Estimated time: {pipeline['est_time']}")
    print(f"Running: scripts/{pipeline['script']}")
    print("-" * 80)
    
    script_start = time.time()
    
    try:
        # Run the script
        result = subprocess.run(
            ['python', f"scripts/{pipeline['script']}"],
            capture_output=False,
            text=True
        )
        
        script_elapsed = time.time() - script_start
        
        if result.returncode == 0:
            status = "✓ SUCCESS"
            success = True
        else:
            status = "✗ FAILED"
            success = False
        
        results.append({
            'script': pipeline['name'],
            'status': status,
            'time': script_elapsed,
            'success': success
        })
        
        print(f"\n{status} - Completed in {script_elapsed/60:.1f} minutes")
        
    except Exception as e:
        script_elapsed = time.time() - script_start
        results.append({
            'script': pipeline['name'],
            'status': "✗ ERROR",
            'time': script_elapsed,
            'success': False
        })
        print(f"\n✗ ERROR: {e}")
    
    print("-" * 80)

total_elapsed = time.time() - start_time

# Summary
print("\n" + "=" * 80)
print("ENRICHMENT PIPELINE COMPLETE")
print("=" * 80)

print(f"\nTotal time: {total_elapsed/60:.1f} minutes")
print(f"Scripts run: {len(results)}")
print(f"Successful: {sum(r['success'] for r in results)}")
print(f"Failed: {sum(not r['success'] for r in results)}")

print("\n" + "-" * 80)
print("SCRIPT RESULTS:")
print("-" * 80)

for r in results:
    print(f"{r['status']:12} {r['script']:40} ({r['time']/60:.1f} min)")

# Check output files
print("\n" + "-" * 80)
print("OUTPUT FILES CREATED:")
print("-" * 80)

enrichment_files = [
    'prior_breach_history.csv',
    'industry_adjusted_returns.csv',
    'analyst_coverage.csv',
    'institutional_ownership.csv',
    'breach_severity_classification.csv',
    'executive_changes.csv',
    'regulatory_enforcement.csv',
    'dark_web_presence.csv',
    'media_coverage.csv',
    'cyber_insurance.csv'
]

for filename in enrichment_files:
    filepath = f'Data/enrichment/{filename}'
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"  ✓ {filename:45} ({size:,} bytes)")
    else:
        print(f"  ✗ {filename:45} (NOT FOUND)")

print("\n" + "=" * 80)

if all(r['success'] for r in results):
    print("✓✓✓ ALL ENRICHMENT COMPLETE - READY FOR MERGE ✓✓✓")
    print("\nNext step: Run scripts/51_merge_enrichments.py")
else:
    print("⚠ SOME SCRIPTS FAILED - CHECK LOGS ABOVE")
    print("\nYou can still proceed with merge using successful scripts")

print("=" * 80)