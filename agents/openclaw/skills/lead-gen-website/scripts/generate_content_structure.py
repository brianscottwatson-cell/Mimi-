#!/usr/bin/env python3
"""Generate a content structure markdown file from a specs JSON.

Usage:
    python generate_content_structure.py <specs_json> <output_md>

Example:
    python generate_content_structure.py specs.json content-structure.md

specs.json format:
{
    "business_name": "Plombier Pro Metz",
    "location": "Metz et alentours",
    "phone": "+33 3 87 00 00 00",
    "pages": [
        {
            "slug": "/",
            "title": "Plombier Pro Metz — Depannage 24h/24",
            "meta_description": "Plombier professionnel...",
            "h1": "Votre plombier de confiance a Metz",
            "type": "homepage",
            "target_keywords": ["plombier metz", "depannage plomberie"],
            "sections": [
                {"heading": "Nos services", "notes": "List all services with brief descriptions"},
                {"heading": "Pourquoi nous choisir", "notes": "Trust signals, experience, guarantees"}
            ]
        }
    ]
}
"""

import json
import sys


def generate_page_section(page: dict) -> str:
    lines = []
    page_type = page.get("type", "page").upper()
    lines.append(f"## {page.get('title', 'Untitled')} ({page_type})")
    lines.append(f"**Slug:** `{page.get('slug', '/')}`")
    lines.append(f"**Meta Description:** {page.get('meta_description', 'TBD')}")
    lines.append(f"**H1:** {page.get('h1', 'TBD')}")

    keywords = page.get("target_keywords", [])
    if keywords:
        lines.append(f"**Target Keywords:** {', '.join(keywords)}")

    min_words = 1000 if page.get("type") == "blog" else 500
    lines.append(f"**Minimum Word Count:** {min_words}")
    lines.append("")

    sections = page.get("sections", [])
    if sections:
        lines.append("### Content Sections")
        for s in sections:
            heading = s.get("heading", "Section")
            notes = s.get("notes", "")
            lines.append(f"- **{heading}**: {notes}")
        lines.append("")

    lines.append("---\n")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    specs_path, output_path = sys.argv[1], sys.argv[2]

    with open(specs_path, "r", encoding="utf-8") as f:
        specs = json.load(f)

    lines = [
        f"# Content Structure — {specs.get('business_name', 'Project')}",
        f"**Location:** {specs.get('location', 'TBD')}",
        f"**Phone:** {specs.get('phone', 'TBD')}",
        f"**Total Pages:** {len(specs.get('pages', []))}",
        "",
        "---\n",
    ]

    for page in specs.get("pages", []):
        lines.append(generate_page_section(page))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Created: {output_path} ({len(specs.get('pages', []))} pages)")


if __name__ == "__main__":
    main()
