#!/usr/bin/env python3
import json
import re
import html
import os
from urllib.parse import unquote
from difflib import get_close_matches

pages_dir = '/workspace/group/chabadpedia-web/pages'

# Get all available article titles
article_titles = set([f[:-5] for f in os.listdir(pages_dir) if f.endswith('.json')])

print("Building smart redirect map with fuzzy matching...")

redirects = {}
verified = []
fuzzy_matches = []
not_found = []

for filename in os.listdir(pages_dir):
    if not filename.endswith('.json'):
        continue

    filepath = os.path.join(pages_dir, filename)
    source_title = filename[:-5]

    try:
        with open(filepath) as f:
            data = json.load(f)

        text = data.get('parse', {}).get('text', {})
        if isinstance(text, dict):
            text = text.get('*', '')

        # Check if this is a redirect page
        if 'הפניה' in text or 'redirectMsg' in text:
            # Extract redirect target
            match = re.search(r'<a href="/index\.php/([^"]+)"[^>]*>([^<]+)</a>', text)
            if match:
                target_raw = match.group(1).strip()
                target_display = html.unescape(match.group(2).strip())

                # First try: exact match
                if target_display in article_titles:
                    redirects[source_title] = target_display
                    verified.append((source_title, target_display))
                else:
                    # Second try: from URL (unquoted)
                    target_from_url = unquote(target_raw).replace('_', ' ')
                    if target_from_url in article_titles:
                        redirects[source_title] = target_from_url
                        verified.append((source_title, target_from_url))
                    else:
                        # Third try: fuzzy match
                        matches = get_close_matches(target_display, article_titles, n=1, cutoff=0.85)
                        if matches:
                            redirects[source_title] = matches[0]
                            fuzzy_matches.append((source_title, target_display, matches[0]))
                        else:
                            not_found.append((source_title, target_display))
    except Exception as e:
        pass

print(f"✓ Exact matches: {len(verified)}")
print(f"✓ Fuzzy matches: {len(fuzzy_matches)}")
print(f"✗ Not found: {len(not_found)}")

# Save to file
output_file = '/workspace/group/chabadpedia-web/redirect_map.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(redirects, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(redirects)} redirects to {output_file}")

# Verify test cases
test_cases = ['770', 'אלי ריבקין', 'בעל שם טוב']
print("\nVerifying test cases:")
for source in test_cases:
    if source in redirects:
        print(f"  '{source}' -> '{redirects[source]}'")
    else:
        print(f"  '{source}' -> NOT FOUND")
