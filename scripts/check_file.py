import os

breach_file = r'Data\DataBreaches.xlsx'
json_folder = r'Data\JSON Files'

print(f"Breach file size: {os.path.getsize(breach_file) / (1024*1024):.2f} MB")
print(f"Breach file exists: {os.path.exists(breach_file)}")

json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
print(f"\nJSON files found: {len(json_files)}")

if json_files:
    first_json = os.path.join(json_folder, json_files[0])
    print(f"First JSON size: {os.path.getsize(first_json) / (1024*1024):.2f} MB")