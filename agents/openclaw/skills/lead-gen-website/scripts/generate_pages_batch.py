#!/usr/bin/env python3
"""Generate multiple similar pages from a template and data file.

Usage:
    python generate_pages_batch.py <template_file> <data_json> <output_dir>

Example:
    python generate_pages_batch.py service-template.tsx services-data.json client/src/pages/

The data JSON should be an array of objects. Each object's keys map to
{{PLACEHOLDER}} tokens in the template file. An additional key "filename"
(required) sets the output file name.
"""

import json
import os
import re
import sys


def render_template(template: str, data: dict) -> str:
    """Replace all {{KEY}} placeholders in template with values from data."""
    result = template
    for key, value in data.items():
        if isinstance(value, (list, dict)):
            value = json.dumps(value, ensure_ascii=False, indent=2)
        result = result.replace(f"{{{{{key}}}}}", str(value))
    # Warn about unreplaced placeholders
    remaining = re.findall(r"\{\{(\w+)\}\}", result)
    if remaining:
        print(f"  Warning: unreplaced placeholders: {remaining}")
    return result


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    template_path, data_path, output_dir = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    with open(data_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    for i, page_data in enumerate(pages):
        filename = page_data.get("filename")
        if not filename:
            print(f"  Skipping entry {i}: no 'filename' key")
            continue

        rendered = render_template(template, page_data)
        out_path = os.path.join(output_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        print(f"  Created: {out_path}")

    print(f"\nDone — {len(pages)} pages generated in {output_dir}")


if __name__ == "__main__":
    main()
