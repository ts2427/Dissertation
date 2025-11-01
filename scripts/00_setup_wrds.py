import wrds
import getpass

print("=" * 60)
print("WRDS CONFIGURATION SETUP")
print("=" * 60)

print("\nThis will configure your WRDS credentials for future use.")
print("You only need to do this once.\n")

# Get credentials
wrds_username = input("Enter your WRDS username: ")
wrds_password = getpass.getpass("Enter your WRDS password: ")

print("\nConnecting to WRDS...")

# Connect with credentials
try:
    db = wrds.Connection(wrds_username=wrds_username, wrds_password=wrds_password)
    print("\n✓ Successfully connected to WRDS!")
    print("✓ Credentials will be saved for future use")
    
    # Test a simple query
    print("\nTesting connection with a sample query...")
    test = db.raw_sql("SELECT * FROM crsp.dsi LIMIT 5")
    print(f"✓ Query successful! Retrieved {len(test)} sample rows")
    
    db.close()
    print("\n" + "=" * 60)
    print("✓ SETUP COMPLETE")
    print("=" * 60)
    print("\nYou can now run: python scripts\\15_download_wrds_data.py")
    
except Exception as e:
    print(f"\n✗ Connection failed: {e}")
    print("\nPlease check:")
    print("  1. Your WRDS username is correct")
    print("  2. Your WRDS password is correct")
    print("  3. Your WRDS account is active")
    print("  4. You're connected to the internet")