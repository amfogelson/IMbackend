import os
import json

# List all .svg files in the current directory
svg_files = [f for f in os.listdir('.') if f.lower().endswith('.svg')]

# Write to list.json
with open('list.json', 'w') as f:
    json.dump({"icons": svg_files}, f, indent=2)

print(f"Wrote {len(svg_files)} SVGs to list.json") 