import os
import requests
import json
import markdown
from bs4 import BeautifulSoup

URL = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/main/2025-01/README.md"
OUTFILE = "data/tds_course_content.json"

print("📥 Downloading course markdown...")
resp = requests.get(URL)
if resp.status_code != 200:
    print(f"❌ Failed, status code {resp.status_code}")
    exit(1)

md_content = resp.text

# Convert markdown to HTML
html = markdown.markdown(md_content, extensions=["fenced_code", "tables"])
soup = BeautifulSoup(html, "html.parser")

# Extract sections by h2 and h3
course_data = []
current_section = {"title": None, "content": ""}
for tag in soup.find_all(["h2", "h3", "p", "ul", "ol", "pre", "blockquote"]):
    if tag.name in ["h2", "h3"]:
        if current_section["title"]:
            course_data.append(current_section)
        current_section = {"title": tag.text.strip(), "content": ""}
    else:
        current_section["content"] += tag.get_text(separator="\n").strip() + "\n"

if current_section["title"]:
    course_data.append(current_section)

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)

# Save as JSON
with open(OUTFILE, "w", encoding="utf-8") as f:
    json.dump(course_data, f, indent=2, ensure_ascii=False)

print(f"✅ Saved {len(course_data)} sections to {OUTFILE}")
