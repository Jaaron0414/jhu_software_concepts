"""
Quick test to get some data
"""
from scrape import scrape_data, save_data

# Scrape just 5 pages to test
print("Scraping 5 pages for testing...")
data = scrape_data(result_type='all', num_pages=5)

print(f"\nScraped {len(data)} entries")

if data:
    print("\n=== First Entry ===")
    for key, val in data[0].items():
        print(f"{key}: {val}")
    
    # Save it
    save_data(data, 'test_data.json')
    print("\nSaved to test_data.json")
else:
    print("No data found!")
