from scrape import scrape_data, save_data

print("Scraping Grad Cafe (30k+ entries, 1500+ pages)...")
data = scrape_data(result_type='all', num_pages=1500)

if data:
    save_data(data, 'applicant_data.json')
    print(f"Done! Scraped {len(data)} entries")
else:
    print("ERROR: No data scraped!")
