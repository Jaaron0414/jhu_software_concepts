"""
Check for more detailed info in the data
"""
import json

data = json.load(open('test_data.json'))

print(f"Total entries: {len(data)}\n")

# Show entries with GPA
gpa_entries = [d for d in data if d.get('gpa')]
print(f"Entries with GPA: {len(gpa_entries)}")
if gpa_entries:
    print("Sample:")
    for entry in gpa_entries[:3]:
        print(f"  {entry['university']} - {entry['program']}")
        print(f"    GPA: {entry['gpa']}, International: {entry['international']}")
        print(f"    Semester: {entry['semester_year']}")

print()

# Show entries with GRE
gre_entries = [d for d in data if d.get('gre_verbal') or d.get('gre_quantitative')]
print(f"Entries with GRE scores: {len(gre_entries)}")
if gre_entries:
    print("Sample:")
    for entry in gre_entries[:3]:
        print(f"  {entry['university']} - {entry['program']}")
        print(f"    GRE V: {entry['gre_verbal']}, Q: {entry['gre_quantitative']}")

print()

# Show diversity
print("International vs American:")
intl = [d for d in data if d.get('international') == True]
american = [d for d in data if d.get('international') == False]
unknown = [d for d in data if d.get('international') is None]
print(f"  International: {len(intl)}")
print(f"  American: {len(american)}")
print(f"  Unknown: {len(unknown)}")

print("\nStatus breakdown:")
statuses = {}
for d in data:
    status = d.get('status', 'Unknown')
    # Extract just the main status word
    main_status = status.split()[0] if status else 'Unknown'
    statuses[main_status] = statuses.get(main_status, 0) + 1
for status, count in sorted(statuses.items(), key=lambda x: -x[1]):
    print(f"  {status}: {count}")
