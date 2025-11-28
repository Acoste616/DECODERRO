import json
from pathlib import Path

dane_dir = Path("dane")
nuggets_file = dane_dir / "rag_nuggets_final.json"

print("Checking JSON structure...")
with open(nuggets_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total items: {len(data)}")
print(f"\nFirst item fields:")
if data:
    first = data[0]
    for key in first.keys():
        value = first[key]
        if isinstance(value, str):
            print(f"  {key}: {value[:50]}...")
        else:
            print(f"  {key}: {value}")
